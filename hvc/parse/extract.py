"""
YAML parser for extract config files
"""

#from standard library
import os
import copy

#from dependencies
import yaml
import numpy as np

#from hvc
from hvc.features.extract import single_syl_features_switch_case_dict
from hvc.features.extract import multiple_syl_features_switch_case_dict
VALID_FEATURES = list(single_syl_features_switch_case_dict.keys()) + \
                 list(multiple_syl_features_switch_case_dict.keys())

path = os.path.abspath(__file__) # get the path of this file
dir_path = os.path.dirname(path) # but then just take the dir

with open(os.path.join(dir_path,'validation.yml')) as val_yaml:
    validate_dict = yaml.load(val_yaml)

with open(os.path.join(dir_path,'feature_groups.yml')) as ftr_grp_yaml:
    valid_feature_groups_dict = yaml.load(ftr_grp_yaml)

################################################################
# validation functions for individual configuration parameters #
################################################################
valid_spect_param_keys = set(['samp_freq',
                              'nperseg',
                              'noverlap',
                              'freq_cutoffs'])

def validate_spect_params(spect_params):
    if type(spect_params) != dict:
        raise TypeeError('value for key \'spect_params\' in config file did '
                         'not parse as a dictionary of parameters, '
                         'it parsed as {}. Check file formatting.'
                         .format(spect_params))

    if set(spect_params.keys()) != valid_spect_param_keys:
        raise KeyError('unrecognized keys in spect_params dictionary')
    else:
        for sp_key, sp_val in spect_params.items():
            if sp_key == 'samp_freq' or sp_key == 'window_size' or sp_key == 'window_step':
                if type(sp_val) != int:
                    raise ValueError('{} in spect_params should be an integer'.format(sp_key))
            elif sp_key == 'freq_cutoffs':
                if len(sp_val) != 2:
                    raise ValueError('freq_cutoffs should be a 2 item list')
                for freq_cutoff in sp_val:
                    if type(freq_cutoff) != int:
                        raise ValueError('freq_cutoff {} should be an int'.format(sp_val))

valid_segment_param_keys = set(['threshold',
                                'min_syl_dur',
                                'min_silent_dur'])

def validate_segment_params(segment_params):
    """validates segmenting parameters

    Parameters
    ----------
    segment_params : dict
        with following keys:
            threshold : int
                amplitudes crossing above this are considered segments
            min_syl_dur : float
                minimum syllable duration, in seconds
            min_silent_dur : float
                minimum duration of silent gap between syllables, in seconds

    Returns
    -------
    nothing if parameters are valid
    else raises error
    """

    if type(segment_params) != dict:
        raise TypeError('segment_params did not parse as a dictionary, '
                        'instead it parsed as {}.'
                        ' Please check config file formatting.'.format(type(val)))

    elif set(segment_params.keys()) != valid_segment_param_keys:
        if set(segment_params.keys()) < valid_segment_param_keys:
            missing_keys = valid_segment_param_keys - set(segment_params.keys())
            raise KeyError('segment_params is missing keys: {}'
                           .format(missing_keys))
        elif valid_segment_param_keys < set(segment_params.keys()):
            extra_keys = set(segment_params.keys()) - segment_param_keys
            raise KeyError('segment_params has extra keys:'
                           .format(extra_keys))
        else:
            invalid_keys = set(segment_params.keys()) - valid_segment_param_keys
            raise KeyError('segment_params has invalid keys:'
                           .format(invalid_keys))
    else:
        for key, val in segment_params.items():
            if key=='threshold':
                if type(val) != int:
                    raise ValueError('threshold should be int but parsed as {}'
                                     .format(type(val)))
            elif key=='min_syl_dur':
                if type(val) != float:
                    raise ValueError('min_syl_dur should be float but parsed as {}'
                                     .format(type(val)))
            elif key=='min_silent_dur':
                if type(val) != float:
                    raise ValueError('min_silent_dur should be float but parsed as {}'
                                     .format(type(val)))

def _validate_todo_list_dict(todo_list_dict,index):
    """
    validates to-do lists

    Parameters
    ----------
    todo_list_dict : dictionary from "to-do" list
    index : index of element (i.e., dictionary) in list of dictionaries

    Returns
    -------
    todo_list_dict : dictionary after validation, may have new keys added if necessary
    """

    required_todo_list_keys = set(validate_dict['required_todo_list_keys'])
    # if required_todo_list_keys is not a subset of todo_list_dict,
    # i.e., if not all required keys are in todo_list_dict
    if not set(todo_list_dict.keys()) >= required_todo_list_keys:
        missing_keys = required_todo_list_keys - set(todo_list_dict.keys())
        raise KeyError('todo_list item #{0} is missing required keys: {1}'
                       .format(index,missing_keys))
    else:
        additional_keys = set(todo_list_dict.keys()) - required_todo_list_keys
        for extra_key in additional_keys:
            if extra_key not in validate_dict['optional_todo_list_keys']:
                raise KeyError('key {} in todo_list item #{} is not recognized'
                               .format(extra_key,index))

    if 'feature_group' not in todo_list_dict:
        if 'feature_list' not in todo_list_dict:
            raise ValueError('todo_list item #{} does not include feature_group or feature_list'
                             .format(index))

    validated_todo_list_dict = copy.deepcopy(todo_list_dict)
    for key, val in todo_list_dict.items():
        # valid todo_list_dict keys in alphabetical order
        if key == 'bird_ID':
            if type(val) != str:
                raise ValueError('Value {} for key \'bird_ID\' is type {} but it'
                                 ' should be a string'.format(val, type(val)))

        elif key=='data_dirs':
            if type(val) != list:
                raise ValueError('data_dirs should be a list')
            else:
                for item in val:
                    if not os.path.isdir(item):
                        raise ValueError('directory {} in {} is not a valid directory.'
                                         .format(item,key))

        elif key == 'feature_group':
            if type(val) != str and type(val) != list:
                raise TypeError('feature_group parsed as {} but it should be'
                                ' either a string or a list. Please check config'
                                ' file formatting.'.format(type(val)))
            elif type(val) == str:
                if val not in valid_feature_groups_dict:
                    raise ValueError('{} not found in valid feature groups'.format(val))
                else:
                    if 'feature_list' in todo_list_dict:
                        raise KeyError('Can\'t have feature_list and feature_gruop in same config')
                    else:
                        feature_list = valid_feature_groups_dict[val]
                        for feature in feature_list:
                            if feature not in VALID_FEATURES:
                                raise ValueError('feature {} not found in valid feature list'.format(feature))
                        validated_todo_list_dict['feature_list'] = feature_list
            elif type(val)==list and len(val)==1: # if user entered list with just one element
                val = val[0]
                if val not in valid_feature_groups_dict:
                    raise ValueError('{} not found in valid feature groups'.format(val))
                else:
                    if 'feature_list' not in todo_list_dict:
                        validated_todo_list_dict['feature_list'] = valid_feature_groups_dict[val]
            elif type(val) == list:
                # if a list of feature groups
                # make feature list that is concatenated feature groups
                # and also add 'feature_group_id' vector for indexing to config
                feature_list = []
                feature_list_group_ID = []
                ftr_grp_ID_dict = {}
                for grp_ind, ftr_grp in enumerate(val):
                    if ftr_grp not in valid_feature_groups_dict:
                        raise ValueError('{} not found in valid feature groups'.format(val))
                    else:
                        feature_list.extend(valid_feature_groups_dict[ftr_grp])
                        feature_list_group_ID.extend([grp_ind] * len(valid_feature_groups_dict[ftr_grp]))
                        ftr_grp_ID_dict[ftr_grp] = grp_ind
                for feature in feature_list:
                    if feature not in VALID_FEATURES:
                        raise ValueError('feature {} not found in valid feature list'.format(feature))
                validated_todo_list_dict['feature_list'] = feature_list
                validated_todo_list_dict['feature_list_group_ID'] = np.asarray(feature_list_group_ID)
                validated_todo_list_dict['feature_list_group_ID_dict'] = ftr_grp_ID_dict

        elif key== 'feature_list':
            if type(val) != list:
                raise ValueError('feature_list should be a list but parsed as a {}'.format(type(val)))
            else:
                for feature in val:
                    if feature not in VALID_FEATURES:
                        raise ValueError('feature {} not found in valid feature list'.format(feature))

        elif key=='file_format':
            if type(val) != str:
                raise ValueError('Value {} for key \'file_format\' is type {} but it'
                                 ' should be a string'.format(val, type(val)))
            else:
                if val not in validate_dict['valid_file_formats']:
                    raise ValueError('{} is not a known audio file format'.format(val))

        elif key=='labelset':
            if type(val) != str:
                raise ValueError('Labelset should be a string, e.g., \'iabcde\'.')
            else:
                validated_todo_list_dict[key] = list(val) # convert from string to list of chars
                validated_todo_list_dict['labelset_int'] = [ord(label) for label in list(val)]

        elif key=='output_dir':
            if type(val) != str:
                raise ValueError('output_dirs should be a string but it parsed as a {}'
                                 .format(type(val)))

        elif key=='segment_params':
            validate_segment_params(val)

        elif key == 'spect_params':
            validate_spect_params(val)

        else: # if key is not found in list
            raise KeyError('key {} in todo_list_dict is an invalid key'.
                            format(key))
    return validated_todo_list_dict

##########################################
# main function that validates yaml file #
##########################################

def validate_yaml(extract_config_yaml):
    """
    validates config from extract YAML file

    Parameters
    ----------
    extract_config_yaml : dictionary, config as loaded with YAML module

    Returns
    -------
    extract_config_dict : dictionary, after validation of all keys
    """

    if 'todo_list' not in extract_config_yaml:
        raise KeyError('extract config does not have required key \'todo_list\'')

    if 'spect_params' not in extract_config_yaml:
        has_spect_params = ['spect_params' in todo_dict
                            for todo_dict in extract_config_yaml['todo_list']]
        if not all(has_spect_params):
            raise KeyError('no default `spect_params` specified, but'
                           'not every todo_list in extract config has spect_params')

    if 'segment_params' not in extract_config_yaml:
        has_segment_params = ['segment_params' in todo_dict
                              for todo_dict in extract_config_yaml['todo_list']]
        if not all(has_segment_params):
            raise KeyError('no default `segment_params` specified, but'
                           'not every todo_list in extract config has segment_params')

    validated_extract_config = copy.deepcopy(extract_config_yaml)
    for key, val in extract_config_yaml.items():
        if key == 'spect_params':
            validate_spect_params(val)
        elif key=='segment_params':
            validate_segment_params(val)
        elif key=='todo_list':
            if type(val) != list:
                raise TypeError('todo_list did not parse as a list, instead it parsed as {}.'
                                ' Please check config file formatting.'.format(type(val)))
            else:
                for index, item in enumerate(val):
                    if type(item) != dict:
                        raise TypeError('item {} in todo_list did not parse as a dictionary, '
                                        'instead it parsed as a {}. Please check config file'
                                        ' formatting'.format(index, type(item)))
                    else:
                        val[index] = _validate_todo_list_dict(item,index)
            validated_extract_config['todo_list'] = val # re-assign because feature list is added

        else: # if key is not found in list
            raise KeyError('key {} in extract is an invalid key'.
                            format(key))

    return validated_extract_config