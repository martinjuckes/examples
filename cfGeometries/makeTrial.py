import xlrd, os
import collections
import netCDF4,numpy
import shapely
import shapely.affinity
from shapely.geometry import Polygon

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from mpl_toolkits.basemap import Basemap, shiftgrid, addcyclic
import numpy as np

class regionsIn(object):
  nt_rec = collections.namedtuple( 'rec', ['title','label','nsres','mask','lon','lat'] )
  def __init__(self):
    wb = xlrd.open_workbook( 'referenceRegions.xls' )
    sht = wb.sheet_by_name('Sheet1')
    self.ll = []
    for i in range(1,sht.nrows):
      r = [str(x.value).strip() for x in sht.row(i)]
      title,lab,ns,mask = r[:4]
      lab = lab[:3]
      x = []
      y = []
      for c in r[4:]:
        if c != '':
          a,b = c.split()
          x.append( float(a) )
          y.append( float(b) )
      self.ll.append( self.nt_rec(title,lab,ns,mask,x,y ) )


class nc1(object):
  def __init__(self,records,fn='regionsTrial.nc'):
    n = 0
    if os.path.isfile(fn):
      os.unlink( fn )
    self.nc = netCDF4.Dataset( fn, 'w')
    self.vars = {}
    for r in records.ll:
      n += len(r.lat)
    dimensions = {'instance':len(records.ll), 'node':n, 'len_lab':3, 'len_des':32 }
    self.dimensions = dimensions

    self.setdims( dimensions )
    self.setattrs( {'Conventions':'CF-1.8',
                    'comment':'Trial implementation of proposed geometries extension to the CF standard, for the IPCC regions (see http://www.ipcc-data.org/guidelines/pages/ar5_regions.html for details). Masking information not yet included'} ) 

    self.addvar( 'node_count', 'int', 'instance', data=[len(r.lat) for r in records.ll] )
    self.addvar( 'region_names', 'char', ('instance','len_lab'), data=[r.label for r in records.ll] )
    self.addvar( 'region_title', 'char', ('instance','len_des'), data=[r.title for r in records.ll] )
    self.addvar( 'crs', 'float', None, data=0., attributes={
                 'grid_mapping_name':"latitude_longitude", 'semi_major_axis':6378137.,
                 'inverse_flattening':298.257223563, 'longitude_of_prime_meridian':0.} )
    self.addvar( 'geometry_container',  'float', None, data=0., attributes={
                  'geometry_type':"polygon", 'node_count':"node_count",
                  'node_coordinates':"x y", 'crs':"crs", 'geometry_attributes':'region_names region_titles'}  )
    lon = []
    lat = []
    for r in records.ll:
      lon += r.lon
      lat += r.lat
    self.addvar( 'lon',  'double', 'node', data=lon, attributes={
    'units':"degrees_east", 'standard_name':"longitude", 'cf_role':"geometry_x_node"} )
    self.addvar( 'lat',  'double', 'node', data=lat, attributes={
    'units':"degrees_north", 'standard_name':"latitude", 'cf_role':"geometry_y_node"} )

    self.close()


  def setdims( self, dd):
    for k in dd:
      self.nc.createDimension( k, size=dd[k] )

  def setattrs( self, dd):
    for k in dd:
      self.nc.setncattr( k, dd[k] )

  def addvar( self, tag, typ, dim, data=None, attributes=None ):
    thistype = {'float':'f', 'double':'d', 'char':'S1', 'int':'i' }[typ]
    if dim == None:
      vlvar = self.nc.createVariable(tag, thistype)
    else:
      if type(dim) == type( () ):
        vlvar = self.nc.createVariable(tag, thistype, dim)
      else:
        vlvar = self.nc.createVariable(tag, thistype, (dim,))
    if attributes != None:
      for k in attributes:
         vlvar.setncattr( k, attributes[k] )
    if data != None:
      if typ == 'char':
        print dim
        print data
        x = numpy.chararray( self.dimensions[dim[0]], itemsize=self.dimensions[dim[1]] )
        x[:] = data
        self.nc.variables[tag][:] = netCDF4.stringtochar(x)
      else:
        self.nc.variables[tag][:] = data
    

  def close(self):
    self.nc.close()
     

class ncin(object):
  nt__rec = collections.namedtuple( 'rec', ['title','label','points'] )
  nt__ip = collections.namedtuple( 'ip', ['val1','title','val2'] )
  def __init__(self,fn='regionsTrial.nc'):
    self.nc = netCDF4.Dataset( fn, 'r')
    self.vars = {}
    self.attr = {}
    self.dimensions = {}
    for k in self.nc.dimensions.keys():
      self.dimensions[k] = len( self.nc.dimensions[k] )

    for k in self.nc.variables.keys():
      ee = {}
      for a in self.nc.variables[k].ncattrs():
        ee[a] = self.nc.variables[k].getncattr( a )
      self.vars[k] = {'data':self.nc.variables[k][:], 'attr':ee}
    self.close()

    self.parseGeom()
    self.shapely()

  def shapely(self):
    self.polys = []
    self.mpolys = []
    self.ipolys = []
    domain = shapely.geometry.box(-180.0,-90.,180.,90.)
    
    colsv = range( len( self.ll ) )
    numpy.random.shuffle( colsv )
    k = 0
    for r in self.ll:
      sp = Polygon(r.points)
      spc = list(sp.exterior.coords)
      lons = [x[0] for x in spc]
      if max(lons) > 180.:
        spa = domain.intersection( sp )
        sp2 = shapely.affinity.translate(sp,xoff=-360)
        spb = domain.intersection( sp2 )
        spc = list(sp2.exterior.coords)

        self.polys.append( spa )
        self.ipolys.append( self.nt__ip( colsv[k], r.title, 'a' ) )
        mp = matplotlib.patches.Polygon(list(spa.exterior.coords))
        mp.set_label( r.label )
        mp.set_facecolor( matplotlib.cm.jet(k*6) )
        self.mpolys.append( mp )

        self.polys.append( spb )
        self.ipolys.append( self.nt__ip( colsv[k], r.title, 'b' ) )
        mp = matplotlib.patches.Polygon(list(spb.exterior.coords))
        mp.set_label( r.label + "'" )
        mp.set_facecolor( matplotlib.cm.jet(k*6) )
        mp.set_edgecolor( matplotlib.cm.jet(k*6) )
        self.mpolys.append( mp )
      else:
        self.polys.append( sp )
        self.ipolys.append( self.nt__ip( colsv[k], r.title, 'a' ) )
 
        mp = matplotlib.patches.Polygon(spc)
        mp.set_label( r.label )
        mp.set_facecolor( matplotlib.cm.jet(k*6) )
        self.mpolys.append( mp )
      k += 1

    fig = plt.figure(figsize =(8,6))
    ax = plt.gca()
    plt.tick_params(direction='out', which='both')

#set up map
    mymap = Basemap(projection='cyl',llcrnrlon=-180, urcrnrlon=180, \
                llcrnrlat=-90, urcrnrlat=90, \
                lon_0=0, lat_0=0, resolution='c')

#colour land, sea and lakes
    mymap.fillcontinents(color='coral',lake_color='aqua')
    mymap.drawmapboundary(fill_color='aqua')
    p = PatchCollection(self.mpolys, cmap=matplotlib.cm.jet, alpha=0.5, zorder=2)

    colors = [x.val1 for x in self.ipolys]
    p.set_array(np.array(colors))

    fp = matplotlib.font_manager.FontProperties( size=8 )
    ax.add_collection(p)
    for k in range(len(self.polys)):
      xc = self.polys[k].centroid.x
      yc = self.polys[k].centroid.y
      plt.text(xc,yc, self.mpolys[k].get_label(), horizontalalignment='center', fontproperties=fp, va='center')

    plt.show()

  def parseGeom(self):
    node_count_name = self.vars['geometry_container']['attr']['node_count']
    node_count = self.vars[node_count_name]['data']
    assert len( node_count ) == self.dimensions['instance'], '%s != %s' % ( len( node_count ), self.dimensions['instance'] )
    assert sum( node_count ) == self.dimensions['node']
    self.ll = []
    ni = self.dimensions['instance']
    i0 = 0
    lon = self.vars['lon']['data'].tolist()
    lat = self.vars['lat']['data'].tolist()
    for k in range( ni):
      i1 = i0 + node_count[k]
      points = []
      for i in range(i0,i1):
        points.append( [lon[i],lat[i]] )

      self.ll.append( self.nt__rec(
           netCDF4.chartostring(self.vars['region_title']['data'][k]).tolist(),
           netCDF4.chartostring(self.vars['region_names']['data'][k]).tolist(),
           points ) )
      i0 = i1
##
## need to break up, using node_count
##
  def close(self):
    self.nc.close()

class pshp(object):
  def __init__(self,mshp):
    plt.figure(figsize=(11, 8))
    plt.tick_params(direction='out', which='both')

#set up map
    mymap = Basemap(projection='cyl',llcrnrlon=-180, urcrnrlon=180, \
                llcrnrlat=-90, urcrnrlat=90, \
                lon_0=0, lat_0=0, resolution='c')

#colour land, sea and lakes
    mymap.fillcontinents(color='coral',lake_color='aqua')
    mymap.drawmapboundary(fill_color='aqua')

##plt.text(43, 55, 'Moscow', horizontalalignment='left', verticalalignment='center')
##plt.plot(37, 55, marker='o', color="red")

    for k in range(len(mshp.ll)):
      xpts=[p[0] for p in mshp.ll[k].points]
      ypts=[p[1] for p in mshp.ll[k].points]
      xpts.append(xpts[0])
      ypts.append(ypts[0])
      plt.plot(xpts,ypts, linewidth=3.0, color='blue', alpha=0.5, )
      xc = mshp.polys[k].centroid.x
      yc = mshp.polys[k].centroid.y
      plt.text(xc,yc, mshp.ll[k].label, horizontalalignment='center')

#axes
    plt.xticks(np.arange(-180, 210, 60), ['180', '120W', '60W', '0', '60E', '120E', '180'])
    plt.yticks(np.arange(-90, 120, 30), ['90S', '60S', '30S', '0', '30N', '60N', '90N'])
#coastlines and title
    mymap.drawcoastlines()

    plt.savefig('ex28.png')
