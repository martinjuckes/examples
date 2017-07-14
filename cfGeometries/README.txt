
The makeTrial.py module contains classes to:
  * read in regions definitions from an ad hoc spreadsheet format;
  * write NetCDF files following (hopefully) the draft CF standard;
  * read in from the draft CF standard
  * plot a global plot.

The plotting places a label at the centroid of each polygon. When polygons span the date line, they are split into two. The python shapely library is used to calculate polygon centroids, and to detect polygons which cross the longitudinal boundaries of the plotting domain, and to split them in this case. 
