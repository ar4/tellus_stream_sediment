# tellus_stream_sediment
Analysis of Ireland's Tellus stream sediment data

The Tellus project has released measurements of the concentration of various substances in stream sediment in [Ireland](http://www.tellus.ie/data) and [Northern Ireland](https://www.opendatani.gov.uk/dataset/gsni-tellus-regional-stream-waters-anion-and-npoc-by-ion-chromatography). Only the coordinates of the sampling locations and the measurements are provided. For many users, such as mineral prospectors, it is the provenance - the location where these substances originated from - that is of interest. Although the data do not directly contain this information, if we combine them with estimates of where the stream water at each measurement location could have come from, we can infer the possible origins.

To do this, I use a flow directions map. This is a map that predicts the direction water will flow in at each point on the landscape. I can then determine the upstream area of each measurement point - the region of the landscape that drains through that point. Making some assumptions, including that all of the measured substance arrived at the measurement point by overland flow, I use this information to make a map of estimated substance concentration.

#Data download
This will contain a link to download the data when they are available.

#How to view
The substance concentration maps are saved in GeoTIFF format, one for each substance, and then compressed into a zip file. Many GIS viewers are able to open the zip file directly. If you are not an experienced GIS user, I provide instructions to view the maps:

1. Download the free, open source [QGIS](https://www.qgis.org) software and install it.
2. Start QGIS
3. Click Layer > Add Raster Layer
4. Download `tellus_sediment.zip` if you have not done so already
4. Find the `tellus_sediment.zip` file and open it
5. All of the substance concentration maps should open as layers
6. Select desired layer
7. To make it easier to see, we will display the layer in colour
8. Right click on the layer and click Properties
9. Click on the Style tab
10. Change from Gray to Pseudo-colour
11. Click OK

#How to run
These are instructions for running the code that generates the output `tellus_sediments.zip` file. You don't need to do this if you are only interested in the data (which you can download above). These instructions are for running on a Linux system. Some modifications may be necessary for other operating systems.

Download the package using the command `git clone https://github.com/ar4/tellus_stream_sediments.git --depth=1`. Then descend into the downloaded directory with `cd tellus_stream_sediments`.

You must download the [HydroSHEDS](http://www.hydrosheds.org) flow directions dataset. This provides the flow directions map. Its license prohibits redistributing it. You have to register on the website before you can download the data. When you have access, download the 3 arcsecond flow directions data tiles covering 50N, 5W to 55N, 15W in BIL format. There should be six tiles. Unzip these files into the data/input directory. The Tellus measurements should already be present in `data/input` (as these have a license that allows distribution).

The source code is written in Python. I use Python 3, but it should probably run with Python 2 as well. Ensure that you have the required packages installed by running `pip install -r requirements.txt`. If you have difficulties, try installing [Anaconda](https://www.continuum.io/downloads), which should provide you with most of the required packages, and then also install GDAL using `conda install gdal`.

Test your installation by running `make test`. All tests should pass.

You should now be able to produce `data/output/tellus_sediments.zip` by simply running `make`. It will take a few hours.

#Details
The flow directions map divides the landscape into grid cells, and assigns a flow direction to each cell. To find the upstream area of a measurement point I therefore examine the eight immediate neighbour cells around the cell that contains the measurement point, to determine which of them drain into the measurement cell. I then examine the neighbours of those that do drain to the measurement point, and find which of their neighbours drain to them. Continuing this recursively, I can find all of the cells on the landscape that drain to a particular measurement point. This is done in `src/find_upstream.py`. Assuming that all of the sediment in the samples comes from overland flow, and ignoring possible spatial variations in erosion and deposition of sediment, I can then determine the likely substance concentration of the upstream cells by solving a linear system consisting of rows like:

`sum_j a_i * x_j = b_i`

where `b_i` is the concentration value of measurement `i`, `x_j` is the concentration of the substance in the `j`th upstream  cell (this is what we want to find), and `a_i` is one over the number of upstream cells for measurement `i`.

I form a system of equations of the form `A*x = b`, and solve it for `x`. I use a solver that is constrained to not produce any negative values, as I do not allow negative substance concentrations. This is done in `src/reverse_sediment.py`.

##Assumptions
I make several assumptions in this analysis. One that has already been mentioned is that all of the sediment arrives at the measurement points by overland flow, not through underground flow. This assumption is necessary because I only know overland flow directions.

Another that was also already mentioned is that erosion and deposition rates are the same at all points. Equal concentrations of a substance at any cell upstream of the measurement point will thus contribute equally to the measured concentration. In reality this is unlikely; much of the sampled sediment probably comes from the fast-flowing mountain streams where erosion is high, and will depend on land cover and usage. Future revisions may incorporate an estimate of erosion rates.

The analysis also relies on the accuracy of the HydroSHEDS flow directions dataset. This assumes that D8 flow directions (flow in each cell is directed entirely into one of its eight neighbours) is a good approximation. I may experiment with using another approach in the future, such as DInf, but these can raise other issues.

The Tellus documents describe the variations between the methods used in Ireland and Northern Ireland to produce the measurements, but I assumed that errors introduced by neglecting these differences were small compared with the other inaccuracies.

#Licenses

##Tellus data (Ireland)
`data/input/GSI_Tellus_2013_StreamSediment_XRFS_FA_ICPMS_geochemical_data_v1.1.csv`
`data/input/GSI_Tellus_2016_StreamSediment_XRFS_FA_ICPMS_geochemical_data_v1.0.csv`

The copyright of these files is owned by the Government of Ireland. It is subject to the Irish PSI license, which allows distribution.

##Tellus data (Northern Ireland)
`data/input/regionalsedimentsxrfset1.csv`
`data/input/regionalsedimentsxrfset2.csv`
`data/input/regionalsedimentsxrfauandpge.csv`

These files are Crown Copyright and subject to the Open Government License for public sector information, which allows distribution. 

##Source code
I have chosen to apply the GPLv3 license to all source code. This may be viewed in the LICENSE file.

##tellus_sediments.zip
I use the CC BY license, which allows you to freely use the substance concentration maps, including in publications, as long as you attribute the work to Alan Richardson (Ausar Geophysical).

This work is licensed under the Creative Commons Attribution 4.0 International License. To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.

This product incorporates data from the HydroSHEDS database which is © World Wildlife
Fund, Inc. (2006-2008). Portions of the HydroSHEDS database incorporate data which are
the intellectual property rights or © USGS (2006-2008), NASA (2000-2005), ESRI (1992-
1998), CIAT (2004-2006), UNEP-WCMC (1993), WWF (2004), Commonwealth of Australia
(2007), and Her Royal Majesty and the British Crown and are used under license.
