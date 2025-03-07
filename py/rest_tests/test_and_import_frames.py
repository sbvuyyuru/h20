####################################################################################################
# Create, import and check datasets
####################################################################################################

import h2o
import h2o_test_utils
from h2o_test_utils import DatasetSpec


def load_and_test(a_node, pp):
    ##################
    # Test CreateFrame
    if h2o_test_utils.isVerbose(): print 'Testing CreateFrame. . .'
    created_job = a_node.create_frame(dest='created') # call with defaults
    
    a_node.poll_job(job_key=created_job['key']['name']) # wait until done and get CreateFrameV3 instance (aka the Job)
    
    frames = a_node.frames(key='created')['frames']
    assert len(frames) == 1, "FAIL: expected to find 1 frame called 'created', found: " + str(len(frames))
    assert frames[0]['frame_id']['name'] == 'created', "FAIL: expected to find 1 frame called 'created', found: " + repr(frames)
    
    created = frames[0]
    assert 'rows' in created, "FAIL: failed to find 'rows' field in CreateFrame result."
    assert created['rows'] == 10000, "FAIL: expected value of 'rows' field in CreateFrame result to be: " + str(10000) + ", found: " + str(created['rows'])
    assert 'columns' in created, "FAIL: failed to find 'columns' field in CreateFrame result."
    assert len(created['columns']) == 10, "FAIL: expected value of 'columns' field in CreateFrame result to be: " + str(10) + ", found: " + str(len(created['columns']))

    # Test CreateFrame -- With Wrong parameter
    param_job = a_node.create_frame(raiseIfNon200=False, dests='created')
    h2o_test_utils.validate_412_statusCode(param_job)
    h2o_test_utils.validate_412_InfoMessage(param_job, "Unknown parameter: dests")
    #########################################################
    # Import and test all the datasets we'll need for the subsequent tests:
    #########################################################
    
    # dest_key, path, expected_rows, model_category, response_column, ignored_columns
    datasets_to_import = [
        DatasetSpec('prostate_clustering', '../../smalldata/logreg/prostate.csv', 380, 'Clustering', None, ['ID']),
        DatasetSpec('prostate_binomial', '../../smalldata/logreg/prostate.csv', 380, 'Binomial', 'CAPSULE', ['ID']),
        DatasetSpec('prostate_regression', '../../smalldata/logreg/prostate.csv', 380, 'Regression', 'AGE', ['ID']),
        DatasetSpec('prostate_delete', '../../smalldata/logreg/prostate.csv', 380, 'Regression', 'AGE', ['ID']),
        DatasetSpec('prostate_spt_negetive', '../../smalldata/logreg/prostate.csv', 380, 'Regression', 'AGE', ['ID']),
        DatasetSpec('airlines_binomial', '../../smalldata/airlines/allyears2k_headers.zip', 43978, 'Binomial', 'IsDepDelayed', ['IsArrDelayed', 'ArrDelay', 'DepDelay']), # TODO: more ignored?
    
        DatasetSpec('iris_multinomial', '../../smalldata/iris/iris_wheader.csv', 150, 'Multinomial', 'class', []),
       ]
    
    datasets = {} # the dataset spec
    for dataset_spec in datasets_to_import:
        dataset = dataset_spec.import_and_validate_dataset(a_node) # it's also stored in dataset_spec['dataset']
        datasets[dataset_spec['dest_key']] = dataset_spec
    
    
    ################################################
    # Test /Frames for prostate.csv
    frames = a_node.frames(row_count=5)['frames']
    frames_dict = h2o_test_utils.list_to_dict(frames, 'frame_id/name')
    
    # TODO: remove:
    if h2o_test_utils.isVerboser():
        print "frames: "
        pp.pprint(frames)
    
    if h2o_test_utils.isVerboser():
        print "frames_dict: "
        pp.pprint(frames_dict)
    
    assert 'prostate_binomial' in frames_dict, "FAIL: Failed to find " + 'prostate_binomial' + " in Frames list."
    assert not frames_dict['prostate_binomial']['is_text'], "FAIL: Parsed Frame is is_text"
    
    
    # Test /Frames/{key} for prostate.csv
    frames = a_node.frames(key='prostate_binomial', row_count=5)['frames']
    frames_dict = h2o_test_utils.list_to_dict(frames, 'frame_id/name')
    assert 'prostate_binomial' in frames_dict, "FAIL: Failed to find prostate.hex in Frames list."
    columns_dict = h2o_test_utils.list_to_dict(frames[0]['columns'], 'label')
    assert 'CAPSULE' in columns_dict, "FAIL: Failed to find CAPSULE in Frames/prostate.hex."
    assert 'AGE' in columns_dict, "FAIL: Failed to find AGE in Frames/prostate.hex/columns."
    assert 'histogram_bins' in columns_dict['AGE'], "FAIL: Failed to find bins in Frames/prostate.hex/columns/AGE."
    h2o.H2O.verboseprint('bins: ' + repr(columns_dict['AGE']['histogram_bins']))
    assert None is columns_dict['AGE']['histogram_bins'], "FAIL: Failed to clear bins field." # should be cleared except for /summary

     # Test /Frames for prostate.csv -- Wrong Parameter
    print("Testing the Bad Parameters.....")
    param_frames = a_node.frames_negetive(row_counts=5)
    h2o_test_utils.validate_412_statusCode(param_frames)
    h2o_test_utils.validate_412_InfoMessage(param_frames, "Unknown parameter: row_counts")
    print("DONE Testing the Bad Parameters.....")
    
    # Test /Frames/{key}/columns for prostate.csv
    frames = a_node.columns(key='prostate_binomial')['frames']
    columns_dict = h2o_test_utils.list_to_dict(frames[0]['columns'], 'label')
    assert 'ID' in columns_dict, "FAIL: Failed to find ID in Frames/prostate.hex/columns."
    assert 'AGE' in columns_dict, "FAIL: Failed to find AGE in Frames/prostate.hex/columns."
    assert 'histogram_bins' in columns_dict['AGE'], "FAIL: Failed to find bins in Frames/prostate.hex/columns/AGE."
    h2o.H2O.verboseprint('bins: ' + repr(columns_dict['AGE']['histogram_bins']))
    assert None is columns_dict['AGE']['histogram_bins'], "FAIL: Failed to clear bins field." # should be cleared except for /summary

    # Test /Frames/{key} for prostate.csv ### worong Parameter
    key_param_frames = a_node.frames_negetive(key='prostate_binomial', row_offsets=10)
    h2o_test_utils.validate_412_statusCode(key_param_frames)
    h2o_test_utils.validate_412_InfoMessage(key_param_frames, "Unknown parameter: row_offsets")
    
    # Test /Frames/{key}/columns/{label} for prostate.csv
    frames = a_node.column(key='prostate_binomial', column='AGE')['frames']
    columns_dict = h2o_test_utils.list_to_dict(frames[0]['columns'], 'label')
    assert 'AGE' in columns_dict, "FAIL: Failed to find AGE in Frames/prostate.hex/columns."
    assert 'histogram_bins' in columns_dict['AGE'], "FAIL: Failed to find bins in Frames/prostate.hex/columns/AGE."
    h2o.H2O.verboseprint('bins: ' + repr(columns_dict['AGE']['histogram_bins']))
    assert None is columns_dict['AGE']['histogram_bins'], "FAIL: Failed to clear bins field." # should be cleared except for /summary

    # Test /Frames/{key}/columns/{label} for prostate.csv ### Wrong param
    col_param_frames = a_node.frames_negetive(key='prostate_binomial', column_counts=3)
    h2o_test_utils.validate_412_statusCode(col_param_frames)
    h2o_test_utils.validate_412_InfoMessage(col_param_frames, "Unknown parameter: column_counts")

    # Test /Frames/{key}/columns/{label}/summary for prostate.csv
    frames = a_node.summary(key='prostate_binomial', column='AGE')['frames']
    columns_dict = h2o_test_utils.list_to_dict(frames[0]['columns'], 'label')
    assert 'AGE' in columns_dict, "FAIL: Failed to find AGE in Frames/prostate.hex/columns/AGE/summary."
    col = columns_dict['AGE']
    h2o_test_utils.assertKeysExistAndNonNull(col, '', ['label', 'missing_count', 'zero_count', 'positive_infinity_count', 'negative_infinity_count', 'mins', 'maxs', 'mean', 'sigma', 'type', 'data', 'precision', 'histogram_bins', 'histogram_base', 'histogram_stride', 'percentiles'])
    h2o_test_utils.assertKeysExist(col, '', ['domain', 'string_data'])
    assert col['mins'][0] == 43, 'FAIL: Failed to find 43 as the first min for AGE.'
    assert col['maxs'][0] == 79, 'FAIL: Failed to find 79 as the first max for AGE.'
    assert abs(col['mean'] - 66.03947368421052) < 1e-8, 'FAIL: Failed to find 66.03947368421052 as the mean for AGE.'
    assert abs(col['sigma'] - 6.527071269173308) < 1e-8, 'FAIL: Failed to find 6.527071269173308 as the sigma for AGE.'
    assert col['type'] == 'int', 'FAIL: Failed to find int as the type for AGE.'
    assert col['data'][0] == 65, 'FAIL: Failed to find 65 as the first data for AGE.'
    assert col['precision'] == -1, 'FAIL: Failed to find -1 as the precision for AGE.'
    assert col['histogram_bins'][0] == 1, 'FAIL: Failed to find 1 as the first bin for AGE.'
    assert col['histogram_base'] == 43, 'FAIL: Failed to find 43 as the histogram_base for AGE.'
    assert col['histogram_stride'] == 1, 'FAIL: Failed to find 1 as the histogram_stride for AGE.'
    assert col['percentiles'][0] == 44.516, 'FAIL: Failed to find 43.516 as the 0.1% percentile for AGE. '+str(col['percentiles'][0])
    assert col['percentiles'][1] == 50.79, 'FAIL: Failed to find 50.79 as the 1.0% percentile for AGE. '+str(col['percentiles'][1])
    assert col['percentiles'][9] == 78, 'FAIL: Failed to find 78 as the 99.0% percentile for AGE. '+str(col['percentiles'][9])
    assert col['percentiles'][10] == 79, 'FAIL: Failed to find 79 as the 99.9% percentile for AGE. '+str(col['percentiles'][10])
    # NB: col['percentiles'] corresponds to probs=[0.001, 0.01, 0.1, 0.25, 0.333, 0.5, 0.667, 0.75, 0.9, 0.99, 0.999]

    # Test /Frames/{key}/columns/{label} for prostate.csv ### Wrong param
    summary_param_frames = a_node.frames_negetive(key='prostate_binomial', find_compatible_model=0)
    h2o_test_utils.validate_412_statusCode(summary_param_frames)
    h2o_test_utils.validate_412_InfoMessage(summary_param_frames, "Unknown parameter: find_compatible_model")

     #Test /Frames/{key}/export for prostate.csv  ### Positive
    job = a_node.export(key='prostate_binomial',
                row_count=100, path="/Users/sureshvuyyuru/export", force="true")['job']
    assert job['dest']['name'] == '/Users/sureshvuyyuru/export', "FAIL: Export Name is not as Expected"
    assert job['description']  == 'Export frame', "FAIL: Frame Descrion is NOT Correct"

     #Test /Frames/{key}/export for prostate.csv  ### Wrong param
    job_negetive = a_node.export(key='prostate_binomial', raiseIfNon200=False,
                row_count=100, path="/Users/sureshvuyyuru/export", forces="true")
    h2o_test_utils.validate_412_statusCode(job_negetive)
    h2o_test_utils.validate_412_InfoMessage(job_negetive, 'Unknown parameter: forces')

    #Suresh domain ### Positive
    # Test /Frames/{key}/columns/{label}/domain for created
    domains = a_node.domain(key='iris_multinomial', raiseIfNon200=False, column='class', row_offset=0, row_count=100)
    domain = domains['domain']
    #pp.pprint(domains)
    assert 'Iris-setosa' in domain[0], "FAIL: Does not find the domain value"
    assert 'Iris-virginica' in domain[0], "FAIL: Does not find the domain Value"
    #Suresh domain ### Negetive
    domains_negetive = a_node.domain(key='iris_multinomial', column='class', domain='Iris-setosa')
    h2o_test_utils.validate_412_statusCode(domains_negetive)
    h2o_test_utils.validate_412_InfoMessage(domains_negetive, 'Attempting to set output field: domain for class: class water.api.FramesV3')


    # Suresh --  ### delete Frame
    #Test DELETE /Frames/{key} for prostate.csv
    resp = a_node.delete_frame(key='prostate_delete')
    assert resp['row_count'] == 0, "FAIL: Row count is not Zero in delete frame"
    assert 'rows' not in resp, "FAIL: Row count is not Zero in delete frame"
    print("prostate_delete Frame has deleted...")

    # Test /SplitFrame for prostate.csv
    if h2o_test_utils.isVerbose(): print 'Testing SplitFrame with named destination_frames. . .'
    splits = a_node.split_frame(dataset='prostate_binomial', ratios=[0.8], destination_frames=['bigger', 'smaller'])
    frames = a_node.frames()['frames']
    h2o_test_utils.validate_frame_exists(a_node, 'bigger', frames)
    h2o_test_utils.validate_frame_exists(a_node, 'smaller', frames)
    bigger = a_node.frames(key='bigger')['frames'][0]
    smaller = a_node.frames(key='smaller')['frames'][0]
    assert bigger['rows'] == 304, 'FAIL: 80/20 SplitFrame yielded the wrong number of rows.  Expected: 304; got: ' + bigger['rows']
    assert smaller['rows'] == 76, 'FAIL: 80/20 SplitFrame yielded the wrong number of rows.  Expected: 76; got: ' + smaller['rows']
    # TODO: h2o_test_utils.validate_job_exists(a_node, splits['frame_id']['name'])
    
    if h2o_test_utils.isVerbose(): print 'Testing SplitFrame with generated destination_frames. . .'
    splits = a_node.split_frame(dataset='prostate_binomial', ratios=[0.5])
    frames = a_node.frames()['frames']
    h2o_test_utils.validate_frame_exists(a_node, splits['destination_frames'][0]['name'], frames)
    h2o_test_utils.validate_frame_exists(a_node, splits['destination_frames'][1]['name'], frames)
    
    first = a_node.frames(key=splits['destination_frames'][0]['name'])['frames'][0]
    second = a_node.frames(key=splits['destination_frames'][1]['name'])['frames'][0]
    assert first['rows'] == 190, 'FAIL: 50/50 SplitFrame yielded the wrong number of rows.  Expected: 190; got: ' + first['rows']
    assert second['rows'] == 190, 'FAIL: 50/50 SplitFrame yielded the wrong number of rows.  Expected: 190; got: ' + second['rows']
    # TODO: h2o_test_utils.validate_job_exists(a_node, splits['frame_id']['name'])
    
    # Test /SplitFrame for prostate.csv ### Split negetive
    print 'Testing SplitFrame with Wrong params...'
    splits_neg = a_node.split_frame( raiseIfNon200=False, dataset='prostate_spt_negetive', ratio=[0.4], destination_frames=['bigger', 'smaller'])
    h2o_test_utils.validate_412_statusCode(splits_neg)
    h2o_test_utils.validate_412_InfoMessage(splits_neg, 'Unknown parameter: ratio')
    #Ratio must be between 0 and 1!
    return datasets
    
