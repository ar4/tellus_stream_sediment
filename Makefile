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
tellus_results = $(output)/tellus_Na2O_%.tif $(output)/tellus_Al2O3_%.tif $(output)/tellus_SiO2_%.tif $(output)/tellus_S_mgkg.tif $(output)/tellus_Cl_mgkg.tif $(output)/tellus_TiO2_%.tif $(output)/tellus_Sc_mgkg.tif $(output)/tellus_V_mgkg.tif $(output)/tellus_Co_mgkg.tif $(output)/tellus_Ga_mgkg.tif $(output)/tellus_Ge_mgkg.tif $(output)/tellus_Br_mgkg.tif $(output)/tellus_Rb_mgkg.tif $(output)/tellus_Sr_mgkg.tif $(output)/tellus_Y_mgkg.tif $(output)/tellus_Zr_mgkg.tif $(output)/tellus_Nb_mgkg.tif $(output)/tellus_Nd_mgkg.tif $(output)/tellus_Sm_mgkg.tif $(output)/tellus_Yb_mgkg.tif $(output)/tellus_Hf_mgkg.tif $(output)/tellus_Ta_mgkg.tif $(output)/tellus_W_mgkg.tif $(output)/tellus_Tl_mgkg.tif $(output)/tellus_Bi_mgkg.tif $(output)/tellus_Th_mgkg.tif $(output)/tellus_Ag_mgkg.tif $(output)/tellus_In_mgkg.tif $(output)/tellus_Te_mgkg.tif $(output)/tellus_I_mgkg.tif $(output)/tellus_Cs_mgkg.tif $(output)/tellus_La_mgkg.tif $(output)/tellus_Au_ugkg.tif $(output)/tellus_Pd_ugkg.tif $(output)/tellus_Pt_ugkg.tif $(output)/tellus_MgO_%.tif $(output)/tellus_P2O5_%.tif $(output)/tellus_K2O_%.tif $(output)/tellus_CaO_%.tif $(output)/tellus_MnO_%.tif $(output)/tellus_Fe2O3_%.tif $(output)/tellus_Cr_mgkg.tif $(output)/tellus_Ba_mgkg.tif $(output)/tellus_Ni_mgkg.tif $(output)/tellus_Cu_mgkg.tif $(output)/tellus_Zn_mgkg.tif $(output)/tellus_As_mgkg.tif $(output)/tellus_Se_mgkg.tif $(output)/tellus_Mo_mgkg.tif $(output)/tellus_Pb_mgkg.tif $(output)/tellus_U_mgkg.tif $(output)/tellus_Cd_mgkg.tif $(output)/tellus_Sn_mgkg.tif $(output)/tellus_Sb_mgkg.tif $(output)/tellus_Ce_mgkg.tif

# inputs
northern_ireland_set1_csv = $(input)/regionalsedimentsxrfset1.csv
northern_ireland_set2_csv = $(input)/regionalsedimentsxrfset2.csv
northern_ireland_auandpge_csv = $(input)/regionalsedimentsxrfauandpge.csv
2013_csv = $(input)/GSI_Tellus_2013_StreamSediment_XRFS_FA_ICPMS_geochemical_data_v1.1.csv
2016_csv = $(input)/GSI_Tellus_2016_StreamSediment_XRFS_FA_ICPMS_geochemical_data_v1.0.csv
tellus_csvs = $(northern_ireland_set1_csv) $(northern_ireland_set2_csv) $(northern_ireland_auandpge_csv) $(2013_csv) $(2016_csv)
hydrosheds_flowdirections = $(input)/n50w005_dir.bil $(input)/n50w010_dir.bil $(input)/n50w015_dir.bil $(input)/n55w005_dir.bil $(input)/n55w010_dir.bil $(input)/n55w015_dir.bil


## Test

# outputs
test_results = $(output)/test_Na2O_%.tif $(output)/test_MgO_%.tif $(output)/test_Al2O3_%.tif $(output)/test_SiO2_%.tif $(output)/test_P2O5_%.tif $(output)/test_S_mgkg.tif


### Targets

all: $(output)/$(name)_sediments.zip

test: test_find_upstream test_reverse_sediment


## Processing flow

# Zip results
$(output)/$(name)_sediments.zip: $($(name)_results) README.md
	mkdir $(name)_sediments
	cp $^ $(name)_sediments
	zip $@ $(name)_sediments
	rm -r $(name)_sediments

# Estimate concentration of measured substance in upstream cells (main result)
$(output)/$(name)_%.tif: $(interim)/$(name)_measurements.csv $(interim)/$(name)_measurements.csv $(interim)/$(name)_upstream.npy $(src)/reverse_sediment.py
	python $(src)/reverse_sediment.py --output=$@ --column=$* --measurements=$(interim)/$(name)_measurements.csv --upstream=$(interim)/$(name)_upstream.npy --flow_directions=$(interim)/$(name)_flow_directions.tif

# Determine upstream raster cells of each point in CSV
# EPSG:29901 is the Irish National Grid
$(interim)/$(name)_upstream.npy: $(interim)/$(name)_measurements.csv $(interim)/$(name)_flow_directions.tif $(src)/find_upstream.py
	python $(src)/find_upstream.py --output=$@ --measurements=$(interim)/$(name)_measurements.csv --measurements_epsg=29901 --flow_directions=$(interim)/$(name)_flow_directions.tif


## Tellus input preparation

# Merge input CSVs into single CSV
$(interim)/tellus_measurements.csv: $(tellus_csvs) $(src)/merge_csvs.py
	python $(src)/merge_csvs.py $@ $(tellus_csvs) --ni1idx=0 --ni2idx=1 --niauandpgeidx=2

# Crop the flow directions to a region around Ireland to reduce file sizes
$(interim)/tellus_flow_directions.tif: $(interim)/tellus_flow_directions_full.tif
	gdalwarp -srcnodata 0 -cutline $(input)/ireland_outline.shp -crop_to_cutline $^ $@

# Merge HydroSHEDS flow directions into single file
$(interim)/tellus_flow_directions_full.tif: $(hydrosheds_flowdirections)
	gdal_merge.py -o $@ $^


## Test input preparation

$(interim)/test_measurements.csv $(interim)/test_flow_directions.tif: $(src)/make_test_dataset.py
	python $(src)/make_test_dataset.py --measurements=$(interim)/test_measurements.csv --flow_directions=$(interim)/test_flow_directions.tif


## Tests

test_find_upstream: $(interim)/test_upstream.npy
	python -m pytest $(src)/test_find_upstream.py --upstream=$(interim)/test_upstream.npy

test_reverse_sediment: $(test_results)
	python -m pytest $(src)/test_reverse_sediment.py --na=$(output)/test_Na2O_%.tif --mg=$(output)/test_MgO_%.tif --al=$(output)/test_Al2O3_%.tif --si=$(output)/test_SiO2_%.tif --p2=$(output)/test_P2O5_%.tif --s_=$(output)/test_S_mgkg.tif

.PHONY: all test test_find_upstream test_reverse_sediment

endif
