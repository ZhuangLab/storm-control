
Some notes about the meaning of various parameters.

1. View versus stage orientation.
  view : flip_horizontal, flip_vertical, transpose
    These only effect how the picture from the camera is displayed, not how
    the data is stored.

  stage : x_sign, y_sign, flip_axis
    These effect (in combination with the view settings) effect how the stage
    moves.

  To get things set up properly you should set all the view orientation settings 
  to 0, then adjust the stage settings so that the stage moves in the expected
  direction when you perform an action like click - drag, or press one of the 
  stage motion arrow buttons.

  Also: Note that neither of these will have any effect on how Steve behaves.
  If Steve is not tyling images correctly the only way to correct this is by
  changing Steve's parameters file.

