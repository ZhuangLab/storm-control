
The Steve software is used for generating image mosaics and
determining how your sample is laid out on a coverslip. The
various settings such as which objectives are available,
which objective is the current objective, camera orientation
and pixel size are contained in the mosaic settings section
of the HAL parameters default file. If HAL is running then
Steve will query HAL to get this information. If HAL is not
running then Steve will look for this information in the
.xml file associated with the movies that are saved by HAL.

"File" -> "Save Positions" will create a list of positions
that you can use with the Dave program.

The scroll wheel on the mouse can be used to zoom in or out
of either the Mosaic or Sections view.

Right clicking on the Mosaic window or the Sections window
will bring up a menu of options. In addition there are a
number of "secret" keys:

 Mosaic tab in front:
  1. After clicking in the view area:
    <space> - Take a picture at the current mouse position.
    <3> - Take a 3x3 grid of pictures around the current mouse
       position.
    <5> - Take a 5x5 grid of pictures.
    <7> - Take a 7x7 grid of pictures.
    <9> - Take a 9x9 grid of pictures.
    <g> - Take a X x Y grid of pictures.
    <p> - Add the current mouse position to the list of 
       positions.
    <s> - Add the current mouse position to the list of
       sections.
  2. After clicking in the positions box:
    <a,w,s,d> - Change the position of the highlighted section.

 Sections tab in front:
  <up arrow> - Change the currently active section.
  <down arrow> - Change the currently active section.
  <q,w,e,a,s,d> - Translate & rotate the section.
  <delete> - Delete the section.
  <space> - Take an images at each section center.
  <3> - Take a 3x3 grid of pictures at each section
     center.
  <5> - Take a 5x5 grid of pictures.
  <g> - Take a X x Y grid of pictures.
