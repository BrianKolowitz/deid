#!/usr/bin/env python3
# This is a complete example of doing de-identifiction. For details, see our docs
# https://pydicom.github.io/deid
import os
import csv
import datetime
import itertools
from pydicom import read_file
from pydicom.uid import generate_uid
from deid.dicom import replace_identifiers, get_files, get_identifiers
from deid.utils import get_installdir
from deid.config import load_deid

def load_look_up_table(lut_path):
    lut = {}
    with open(lut_path, 'r') as f:
        reader = csv.reader(f)
        for i, row in zip(itertools.count(), reader):
            if i == 0:
                continue # skip header
            lut[row[0]] = row[1]
    return lut

def look_up_value(lut, lookup_key):
    if lookup_key in lut:
        return lut[lookup_key]
    raise Exception('%s not found' %lookup_key)

def deid_data(data_path,
              output_path,
              deid_path,
              config_file_path,
              clean_output_directory,
              lut_patient_id,
              lut_accession_number):

    # Get the dicom files
    dicom_files = get_files(data_path)

    # This is the function to get identifiers
    ids = get_identifiers(dicom_files)

    #**
    # Here you might save the identifiers in your special (IRB approvied) places
    # And then provide replacement anonymous ids to put back in the data
    #**

    # If you are intereseted to see it, but you don't have to do this,
    # this happens internally
    deid = load_deid(deid_path)

    # Let's add the fields that we specify to add in our deid, a source_id for SOPInstanceUID,
    # and an id for PatientID
    count = 0
    updated_ids = dict()
    for image, fields in ids.items():
        fields['patient_birth_date'] = datetime.datetime.now()
        fields['study_date'] = datetime.datetime.now()
        fields['patient_id'] = look_up_value(lut_patient_id, fields['PatientID'])
        fields['patient_name'] = "pname-%s" %(fields['patient_id'])
        fields['patient_sex'] = "O"
        fields['accession_number'] = look_up_value(lut_accession_number, fields['AccessionNumber'])
        fields['sop_instance_uid'] = generate_uid()
        updated_ids[image] = fields
        count += 1

    if clean_output_directory:
        output_files = os.listdir(output_path)
        for output_file in output_files:
            os.remove(os.path.join(output_path, output_file))

    # Run providing the path to deid, config, and the updated ids
    cleaned_files = replace_identifiers(dicom_files=dicom_files,
                                        ids=updated_ids,
                                        deid=deid,
                                        config=config_file_path,
                                        remove_private=True,
                                        output_folder=output_path)
    return cleaned_files

def dump_file(dicom_file_path, fields):
    dicom_file = read_file(dicom_file_path)
    print(dicom_file_path)
    for field in fields:
        print(dicom_file.data_element(field))
    print()

if __name__ == "__main__":
    lut_patient_id_path = os.path.abspath('%s/Documents/_data/deid_config/lut_patient_id.csv' %os.path.expanduser('~'))
    lut_accession_number_path = os.path.abspath('%s/Documents/_data/deid_config/lut_accession_number.csv' %os.path.expanduser('~'))
    lut_patient_id = load_look_up_table(lut_patient_id_path)
    lut_accession_number = load_look_up_table(lut_accession_number_path)

    data_path = os.path.abspath('%s/Documents/_data/phi_test' %os.path.expanduser('~'))
    output_path = os.path.abspath('%s/Documents/_data/out' %os.path.expanduser('~'))
    deid_path = os.path.abspath("%s/../my_examples/deid/" %get_installdir())
    config_file_path = os.path.abspath("%s/../my_examples/dicom/config.json" %get_installdir())
    clean_output_directory = True

    cleaned_files = deid_data(data_path,
                              output_path,
                              deid_path,
                              config_file_path,
                              clean_output_directory,
                              lut_patient_id,
                              lut_accession_number)

    for cleaned_file in cleaned_files:
        dump_file(cleaned_file, ['PatientID',
                                 'PatientName',
                                 'PatientBirthDate',
                                 'PatientSex',
                                 'AccessionNumber',
                                 'StudyDate',
                                 'SOPInstanceUID'])
