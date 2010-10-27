import os
import difflib
import simplejson as json

d = difflib.Differ()

def filepath(filename):
    return os.path.join('tests', 'data', 'handlers', filename)

def read_file(filename):
    fp = filepath(filename)
    return open(fp, "r").read()

def read_input_file(filename):
    return read_file(filename)

def read_output_dict(filename):
    out_filename = filename.replace('.txt', '.out')
    json_filename = filename.replace('.txt', '.json')
    if os.path.exists(filepath(out_filename)):
        output_text = read_file(out_filename)
        output_dict = { '1' : output_text }
    elif os.path.exists(filepath(json_filename)):
        output_dict = json.load(open(filepath(json_filename), "r"))
    else:
        raise Exception("either %s or %s should exist" % (out_filename, json_filename))

    return output_dict

def read_output_text(filename):
    return read_output_dict(filename)['1']

def test_process_text(h, input_filename):
    input_text = read_file(input_filename)
    output_text = read_output_text(input_filename)
    assert h.process_text(input_text) == output_text

def test_process_dict(h, input_filename):
    input_text = read_file(input_filename)
    input_dict = { '1' : input_text }
    output_dict = read_output_dict(input_filename)
    assert h.process_dict(input_dict) == output_dict

def test_process(h, input_filename, expected_method = None):
    input_text = read_file(input_filename)
    output_text = read_output_text(input_filename)

    if not hasattr(h, 'artifact'):
        h.set_input_text(input_text)
    else:
        input_dict = { '1' : input_text }
        h.artifact.input_data_dict = input_dict
        
    process_result = h.process()
    
    assert h.artifact.output_text() == output_text
    if expected_method:
        assert process_result == expected_method
