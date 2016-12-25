
The Dave software is used to control Hal for automated acquisitions.

You use it by loading (or generating) XML experiment descriptor files.

You can generate a sample XML experiment descriptor file be selecting 
"Generate" in the XML menu, and then following the prompts. First, 
select the file called "positions.txt" (which records where you want 
each of the images / movies to be taken). Second, select a XML file like 
"conv_experiment.xml" or "storm_experiment.xml", and finally choose a 
name to save the generated XML file as.

The typical usage is that you generate a list of locations where you 
would like to take data (the "positions.txt" file, which can be created 
manually, programmatically, or using the Steve program). Then you create 
a XML file like "conv_experiment.xml" which defines what you want to 
happen at each position. Finally you use the XML generation feature to 
create the XML file that Dave will then use to collect the data.
