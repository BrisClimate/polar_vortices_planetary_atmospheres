'''
Planetary polar vortices: Mars PV map
'''
import numpy as np
import xarray as xr
import os, sys

import colorcet as cc
import string

from cartopy import crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import (cm, colors)
import matplotlib.path as mpath

from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


class nf(float):
    def __repr__(self):
        s = f'{self:.1f}'
        return f'{self:.0f}' if s[-1] == '0' else s

def stereo_plot():
    '''
    Returns variables to define a circular plot in matplotlib.
    '''
    theta = np.linspace(0, 2*np.pi, 100)
    center, radius = [0.5, 0.5], 0.5
    verts = np.vstack([np.sin(theta), np.cos(theta)]).T
    circle = mpath.Path(verts * radius + center)
    return theta, center, radius, verts, circle

def make_stereo_plot(ax, lats, lons, circle, **kwargs):
    '''
    Makes the polar stereographic plot and plots gridlines at choice of lats
    and lons.
    '''
    linewidth = kwargs.pop('linewidth', 1)
    linestyle = kwargs.pop('linestyle', '-')
    color = kwargs.pop('color', 'black')
    alpha = kwargs.pop('alpha', 1)

    gl = ax.gridlines(crs = ccrs.PlateCarree(), linewidth = linewidth,
                      linestyle = linestyle, color = color, alpha = alpha)

    ax.set_boundary(circle, transform=ax.transAxes)

    gl.ylocator = ticker.FixedLocator(lats)
    gl.xlocator = ticker.FixedLocator(lons)

def calc_jet_lat(u, lats, plot=False):
    """Function to calculate location and strenth of maximum given zonal wind
    u(lat) field """
    # Restict to 10 points around maximum
    u_max = np.where(u == np.ma.max(u))[0][0]
    u_near = u[u_max-1:u_max+2]
    lats_near = lats[u_max-1:u_max+2]
    # Quartic fit, with smaller lat spacing
    coefs = np.ma.polyfit(lats_near,u_near,2)
    fine_lats = np.linspace(lats_near[0], lats_near[-1],200)
    quad = coefs[2]+coefs[1]*fine_lats+coefs[0]*fine_lats**2
    # Find jet lat and max
    jet_lat = fine_lats[np.where(quad == max(quad))[0][0]]
    jet_max = coefs[2]+coefs[1]*jet_lat+coefs[0]*jet_lat**2
    # Plot fit?
    if plot:
        print (jet_max)
        print (jet_lat)
        plt.plot(lats_near, u_near)
        plt.plot(fine_lats, quad)
        plt.show()

    return jet_lat, jet_max
  
def make_colourmap(vmin, vmax, step, **kwargs):
    '''
    Makes a colormap from ``vmin`` (inclusive) to ``vmax`` (exclusive) with
    boundaries incremented by ``step``. Optionally includes choice of color and
    to extend the colormap.
    '''
    col = kwargs.pop('col', 'viridis')
    extend = kwargs.pop('extend', 'both')

    boundaries = list(np.arange(vmin, vmax, step))

    if extend == 'both':
        cmap_new = cm.get_cmap(col, len(boundaries) + 1)
        colours = list(cmap_new(np.arange(len(boundaries) + 1)))
        cmap = colors.ListedColormap(colours[1:-1],"")
        cmap.set_over(colours[-1])
        cmap.set_under(colours[0])

    elif extend == 'max':
        cmap_new = cm.get_cmap(col, len(boundaries))
        colours = list(cmap_new(np.arange(len(boundaries))))
        cmap = colors.ListedColormap(colours[:-1],"")
        cmap.set_over(colours[-1])

    elif extend == 'min':
        cmap_new = cm.get_cmap(col, len(boundaries))
        colours = list(cmap_new(np.arange(len(boundaries))))
        cmap = colors.ListedColormap(colours[1:],"")
        cmap.set_under(colours[0])

    norm = colors.BoundaryNorm(boundaries, ncolors = len(boundaries) - 1,
                               clip = False)

    return boundaries, cmap_new, colours, cmap, norm
  
def lait(PV,theta,theta0, **kwargs):
    r"""Perform Lait scaling of PV
    kwargs
    ------
    kappa: R/c_p, optional, defaults to 0.25.
    """
    kappa = kwargs.pop('kappa', 0.25)
    ret = PV*(theta/theta0)**(-(1+1/kappa))

    return ret

if __name__ == "__main__":


    Lsmin = 255
    Lsmax = 285

    theta0 = 200.
    kappa = 1/4.0
    p0 = 610.

    ilev = 350



    PATH = '/export/anthropocene/array-01/xz19136/OpenMARS/Isentropic'
    infiles = '/isentropic*'

    figpath = 'OpenMARS_figs/'

    d = xr.open_mfdataset(PATH+infiles, decode_times=False, concat_dim='time',
                           combine='nested',chunks={'time':'auto'})


    # reduce dataset
    d = d.astype('float32')
    d = d.sortby('time', ascending=True)
    d = d.where(d.Ls <= Lsmax, drop=True)
    d = d.where(Lsmin <= d.Ls, drop=True)
    x = d.sel(ilev=ilev, method='nearest')
    x = x.sel(lat=x.lat[50<x.lat])
    x = x.where(x.MY >= 28, drop = True)
    latm = d.lat.max().values

    theta, center, radius, verts, circle = stereo_plot()


    fig, axs = plt.subplots(nrows=1,ncols=2, figsize = (14,8),
                            subplot_kw = {'projection':ccrs.NorthPolarStereo()})



    vmin = 0
    vmax = 81
    step = 5

    boundaries0, _, _, cmap0, norm0 = make_colourmap(vmin, vmax, step,
                                                col = 'OrRd', extend = 'both')



    if plt.rcParams["text.usetex"]:
        fmt = r'%r \%'
    else:
        fmt = '%r'


    # Lait scale PV
    theta = x.ilev
    laitPV = lait(x.PV,theta,theta0,kappa=kappa)
    x["scaled_PV"]=laitPV

    for i, ax in enumerate(fig.axes):
        make_stereo_plot(ax, [latm, 80, 70, 60, 50],
                        [-180, -120, -60, 0, 60, 120, 180],
                        circle, alpha = 0.3, linestyle = '--',)
        ax.text(0.05, 0.95, string.ascii_lowercase[i], transform=ax.transAxes, 
                        size=20, weight='bold')

        if i == 0:
            my = 28
            x0 = x.where(d.MY==my,drop=True).mean(dim='time')
            my = str(my)
        else:
            my = "29-32"
            x0 = x.where(d.MY>28,drop=True).mean(dim='time')
        
        a0 = x0.scaled_PV*10**5

        ax.set_title('MY '+my,weight='bold',fontsize=20)
        

        ax.contourf(a0.lon,a0.lat,a0,transform=ccrs.PlateCarree(),
                    cmap=cmap0,levels=[-50]+boundaries0+[150], norm=norm0)
        c0 = ax.contour(x0.lon, x0.lat, x0.uwnd,levels=[0,40,80,120],colors='0.1',
                        transform=ccrs.PlateCarree(),linewidths = 0.8)

        c0.levels = [nf(val) for val in c0.levels]

        ax.clabel(c0, c0.levels, inline=1, fmt=fmt, fontsize=16)
        
        plt.savefig(figpath + 'PV_mars_map_'+str(ilev)+'K_Ls'+str(Lsmin)+'-'+str(Lsmax)+'.png',
                bbox_inches='tight', pad_inches = 0.02)

    plt.subplots_adjust(hspace=.17,wspace=.04)#, bottom=0.1)



    cb = fig.colorbar(cm.ScalarMappable(norm=norm0,cmap=cmap0),ax=axs,
                      extend='both',aspect=20,shrink=0.8,
                      ticks=boundaries0[slice(None,None,2)],pad=.03)

    cb.set_label(label='Lait-scaled PV (10$^{-5}$ K m$^2$ kg$^{-1}$ s$^{-1}$)',
                 fontsize=17)

    cb.ax.tick_params(labelsize=15)



    plt.savefig(figpath + 'PV_mars_map_'+str(ilev)+'K_Ls'+str(Lsmin)+'-'+str(Lsmax)+'.png',
                bbox_inches='tight', pad_inches = 0.02)
