from __future__ import print_function, division

import yaml
import sys
import subprocess

def get_var_dict(v, source):
    var_dict = {
        'header': {
            'name': v
        }
    }
    if source['units'] is not None:
        var_dict['header']['units'] = source['units']

    var_dict['values'] = []
    for data_tup in source['data']:
        val_row = {}
        if len(data_tup) == 3:
            val_row['low']  = data_tup[0]
            val_row['high'] = data_tup[1]
            errors = data_tup[2]
        elif len(data_tup) == 2:
            val_row['value']  = data_tup[0]
            errors = data_tup[1]
        else:
            raise ValueError
        if len(errors) > 0:
            val_row['errors'] = []
            for error_name, error_plus, error_minus in errors:
                val_row['errors'].append({
                    'asymerror': {
                        'plus': error_plus,
                        'minus': error_minus
                    },
                    'label': error_name
                })
        var_dict['values'].append(val_row)
    return var_dict

def save_to_yaml(data,
                 independent_vars,
                 dependent_vars,
                 out_path):

    output = {
        'independent_variables': [],
        'dependent_variables': []
    }
    for var_type_label, var_types_list in [('independent_variables', independent_vars), ('dependent_variables', dependent_vars)]:
        for v in var_types_list:
            output[var_type_label].append(get_var_dict(v, data[v]))

    if '/' in out_path:
        out_dir = '/'.join(out_path.split('/')[:-1])
        subprocess.check_call('mkdir -p {od}'.format(od=out_dir), shell=True, executable='/bin/bash')
    with open(out_path, 'w') as yaml_output_handle:
        yaml.dump(output, stream=yaml_output_handle, indent=2, default_flow_style=False)

def test_save_to_yaml():
    print('Testing ...')
    data = {
        'x': {
            'units': 'GeV',
            'data': [
                (1000., 1050., []),
                (1050., 1100., []),
                (1050., 1100., [])
            ]
        },
        'y': {
            'units': 'GeV',
            'data': [
                (1000., 1050., []),
                (1000., 1050., []),
                (1050., 1100., [])
            ]
        },
        'z1': {
            'units': None,
            'data': [
                (0.01, []),
                (0.02, []),
                (0.015, [])
            ]
        },
        'z2': {
            'units': 'pbinv',
            'data': [
                (0.01,  [('unc1', 0.005, 0.005)]),
                (0.02,  [('unc1', 0.005, 0.005), ('unc2', 0.01, 0.01)]),
                (0.015, [('unc1', 0.005, 0.005), ('unc2', 0.001, 0.001), ('unc3', 0.01, 0.01)])
            ]
        }
    }
    independent_vars = ['x', 'y']
    dependent_vars = ['z1', 'z2']
    out_path = '../tmPyUtilsTests/test_yaml.yaml'
    save_to_yaml(data, independent_vars, dependent_vars, out_path)
    print('Test output saved to: {op}'.format(op=out_path))

if __name__ == '__main__':
    test_save_to_yaml()
