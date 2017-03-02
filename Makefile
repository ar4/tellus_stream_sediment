### Variables

proj_dir = $(PWD)
input = $(proj_dir)/data/input
interim = $(proj_dir)/data/interim
output = $(proj_dir)/data/output
src = $(proj_dir)/src

ifndef name

.PHONY: all test clean

# rerun Make with 'name' set to 'tellus' or 'test'
all: export name = tellus
all:
	@$(MAKE)
test: export name = test
test:
	@$(MAKE) test

clean:
	rm -f $(output)/* $(interim)/*

else

## Tellus

# outputs
tellus_results = $(output)/Na2O_%.tif $(output)/Al2O3_%.tif $(output)/SiO2_%.tif $(output)/S_mgkg.tif $(output)/Cl_mgkg.tif $(output)/TiO2_%.tif $(output)/Sc_mgkg.tif $(output)/V_mgkg.tif $(output)/Co_mgkg.tif $(output)/Ga_mgkg.tif $(output)/Ge_mgkg.tif $(output)/Br_mgkg.tif $(output)/Rb_mgkg.tif $(output)/Sr_mgkg.tif $(output)/Y_mgkg.tif $(output)/Zr_mgkg.tif $(output)/Nb_mgkg.tif $(output)/Nd_mgkg.tif $(output)/Sm_mgkg.tif $(output)/Yb_mgkg.tif $(output)/Hf_mgkg.tif $(output)/Ta_mgkg.tif $(output)/W_mgkg.tif $(output)/Tl_mgkg.tif $(output)/Bi_mgkg.tif $(output)/Th_mgkg.tif $(output)/Ag_mgkg.tif $(output)/In_mgkg.tif $(output)/Te_mgkg.tif $(output)/I_mgkg.tif $(output)/Cs_mgkg.tif $(output)/La_mgkg.tif $(output)/Au_ugkg.tif $(output)/Pd_ugkg.tif $(output)/Pt_ugkg.tif $(output)/MgO_%.tif $(output)/P2O5_%.tif $(output)/K2O_%.tif $(output)/CaO_%.tif $(output)/MnO_%.tif $(output)/Fe2O3_%.tif $(output)/Cr_mgkg.tif $(output)/Ba_mgkg.tif $(output)/Ni_mgkg.tif $(output)/Cu_mgkg.tif $(output)/Zn_mgkg.tif $(output)/As_mgkg.tif $(output)/Se_mgkg.tif $(output)/Mo_mgkg.tif $(output)/Pb_mgkg.tif $(output)/U_mgkg.tif $(output)/Cd_mgkg.tif $(output)/Sn_mgkg.tif $(output)/Sb_mgkg.tif $(output)/Ce_mgkg.tif

# inputs
northern_ireland_csv = $(input)/Regional_Sediments_XRF.csv
2013_csv = $(input)/GSI_Tellus_2013_StreamSediment_XRFS_FA_ICPMS_geochemical_data_v1.1.csv
2016_csv = $(input)/GSI_Tellus_2016_StreamSediment_XRFS_FA_ICPMS_geochemical_data_v1.0.csv
tellus_csvs = $(northern_ireland_csv) $(2013_csv) $(2016_csv)
hydrosheds_flowdirections = $(input)/n50w005_dir.bil $(input)/n50w010_dir.bil $(input)/n50w015_dir.bil $(input)/n55w005_dir.bil $(input)/n55w010_dir.bil $(input)/n55w015_dir.bil


## Test

# outputs
test_results = $(output)/test_Na2O_%.tif $(output)/test_MgO_%.tif $(output)/test_Al2O3_%.tif


### Targets

all: $(output)/$(name)_sediments.zip

test: test_find_upstream test_reverse_sediment


## Processing flow

# Zip results
$(output)/$(name)_sediments.zip: $(name)_$(results) README.md LICENSE
	@echo mkdir $(output)/$(name)_sediments
	@echo cp $^ $(output)/$(name)_sediments
	@echo zip $@ $(output)/$(name)_sediments
	@echo rm -r $(output)/$(name)_sediments

# Estimate abundance of measured substance in upstream cells (main result)
$(output)/$(name)_%.tif: $(interim)/$(name)_measurements.csv $(interim)/$(name)_measurements.csv $(interim)/$(name)_upstream.npy $(src)/reverse_sediment.py
	python $(src)/reverse_sediment.py --output=$@ --column=$* --measurements=$(interim)/$(name)_measurements.csv --upstream=$(interim)/$(name)_upstream.npy --flow_directions=$(interim)/$(name)_flow_directions.tif

# Determine upstream raster cells of each point in CSV
# EPSG:29901 is the Irish National Grid
$(interim)/$(name)_upstream.npy: $(interim)/$(name)_measurements.csv $(interim)/$(name)_flow_directions.tif $(src)/find_upstream.py
	python $(src)/find_upstream.py --output=$@ --measurements=$(interim)/$(name)_measurements.csv --measurements_epsg=29901 --flow_directions=$(interim)/$(name)_flow_directions.tif


## Tellus input preparation

# Merge input CSVs into single CSV
$(interim)/tellus_measurements.csv: $(tellus_csvs) $(src)/merge_csvs.py
	@echo python $(src)/merge_csvs.py $@ $^

# Crop the flow directions to a region around Ireland to reduce file sizes
$(interim)/tellus_flow_directions.tif: $(interim)/tellus_flow_directions_full.tif
	@echo gdalwarp -srcnodata 0 -cutline $(input)/ireland_outline.shp -crop_to_cutline $^ $@

# Merge HydroSHEDS flow directions into single file
$(interim)/tellus_flow_directions_full.tif: $(hydrosheds_flowdirections)
	@echo gdal_merge.py -o $@ $^


## Test input preparation

$(interim)/test_measurements.csv $(interim)/test_flow_directions.tif: $(src)/make_test_dataset.py
	python $(src)/make_test_dataset.py --measurements=$(interim)/test_measurements.csv --flow_directions=$(interim)/test_flow_directions.tif


## Tests

test_find_upstream: $(interim)/test_upstream.npy
	python -m pytest $(src)/test_find_upstream.py --upstream=$(interim)/test_upstream.npy

test_reverse_sediment: $(test_results)
	python -m pytest $(src)/test_reverse_sediment.py --na=$(output)/test_Na2O_%.tif --mg=$(output)/test_MgO_%.tif --al=$(output)/test_Al2O3_%.tif

.PHONY: all test test_find_upstream test_reverse_sediment

endif
