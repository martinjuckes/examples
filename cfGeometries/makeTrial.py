import xlrd, os
import collections
import netCDF4,numpy

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
     

