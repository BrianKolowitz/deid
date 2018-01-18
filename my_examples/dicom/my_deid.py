#!/usr/bin/env python3
# This is a complete example of doing de-identifiction. For details, see our docs
# https://pydicom.github.io/deid
import os
import csv
import datetime
import itertools
import time
import platform

from pydicom import read_file
from pydicom.uid import generate_uid
from deid.dicom import replace_identifiers, get_identifiers
from deid.utils import get_installdir
from deid.config import load_deid
from . import LookupTable


def deid_data(input_path,
              output_path,
              deid_path,
              config_file_path,
              lut_patient_id,
              lut_accession_number):
    # If you are intereseted to see it, but you don't have to do this,
    # this happens internally
    deid = load_deid(deid_path)

    # Get the dicom files
    for index, dicom_file in zip(itertools.count(), get_files(input_path)):
        # This is the function to get identifiers
        dicom_file_ids = get_identifiers(dicom_file)
        #**
        # Here you might save the identifiers in your special (IRB approvied) places
        # And then provide replacement anonymous ids to put back in the data
        #**

        # Let's add the fields that we specify to add in our deid, a source_id for SOPInstanceUID,
        # and an id for PatientID
        for (image, fields) in dicom_file_ids.items():
            fields['patient_birth_date'] = datetime.datetime.now()
            fields['study_date'] = datetime.datetime.now()
            fields['patient_id'] = lut_patient_id.look_up_value(fields['PatientID'], fail=False, add=True, value_format='p{:06d}')
            fields['patient_name'] = "pname-%s" %(fields['patient_id'])
            fields['patient_sex'] = "O"
            fields['accession_number'] = lut_accession_number.look_up_value(fields['AccessionNumber'], fail=False, add=True, value_format='a{:06d}')
            fields['sop_instance_uid'] = generate_uid()
            fields['institution_name'] = 'ACME'
            fields['station_name'] = 'Zenith EZ PC'
            dicom_file_ids[image] = fields

        # Run providing the path to deid, config, and the updated ids
        cleaned_files = replace_identifiers(dicom_files=dicom_file,
                                            ids=dicom_file_ids,
                                            deid=deid,
                                            config=config_file_path,
                                            remove_private=True,
                                            output_folder=output_path)


        cleaned_file_names = [os.path.basename(f) for f in cleaned_files]
        # iterate through the cleaned files and add a cleaned flag
        pad_width = 5
        for (image, fields) in dicom_file_ids.items():
            if image in cleaned_file_names:
                fields['cleaned'] = True
                fields['original_file_path'] = os.path.join(input_path, image)
                fields['cleaned_file_path'] = os.path.join(output_path, image)
                fields['renamed_file_path'] = os.path.join(output_path, "%s.dcm" %str(index).zfill(pad_width))
                os.rename(fields['cleaned_file_path'], fields['renamed_file_path'])
            else:
                fields['cleaned'] = False
                fields['original_file_path'] = os.path.join(input_path, image)
                fields['cleaned_file_path'] = os.path.join(output_path, image)
                fields['renamed_file_path'] = None
            dicom_file_ids[image] = fields
        yield dicom_file_ids

def dump_file(dicom_file_path, fields):
    file_tags = dict()
    dicom_file = read_file(dicom_file_path)
    print(dicom_file_path)
    for field in fields:
        if field in dicom_file:
            element = dicom_file.data_element(field)
            file_tags[field] = element.value
            print(element)
        else:
            file_tags[field] = ''
            print("%s not found" %field)
    print()
    return file_tags

def get_values(dict, keys):
    values = []
    for key in keys:
        if key in dict:
            values.append(str(dict[key]))
        else:
            values.append('')
    return values
            

if __name__ == "__main__":
    osx = platform.system().lower() == 'darwin'
    if osx:
        # osx
        deid_path = os.path.abspath("%s/../my_examples/deid/" %get_installdir())
        config_file_path = os.path.abspath("%s/../my_examples/dicom/config.json" %get_installdir())
        input_path = os.path.abspath('%s/Documents/_data/phi' %os.path.expanduser('~'))
        output_path = os.path.abspath('%s/Documents/_data/out' %os.path.expanduser('~'))
        lut_patient_id_path = os.path.abspath('%s/Documents/_data/deid_config/lut_patient_id.csv' %os.path.expanduser('~'))
        lut_accession_number_path = os.path.abspath('%s/Documents/_data/deid_config/lut_accession_number.csv' %os.path.expanduser('~'))
    else:
        # win
        deid_path = os.path.abspath("%s\\..\\my_examples\\deid" %get_installdir())
        config_file_path = os.path.abspath("%s\\..\\my_examples\\dicom\\config.json" %get_installdir())
        input_path = os.path.abspath('f:\\data\\filtered\\whitelist')
        output_path = os.path.abspath('f:\\data\\out')
        lut_patient_id_path = os.path.abspath('f:\\data\\deid_config\\lut_patient_id.csv')
        lut_accession_number_path = os.path.abspath('f:\\data\\deid_config\\lut_accession_number.csv')

    lut_patient_id = LookupTable()
    lut_patient_id.load(lut_patient_id_path)
    lut_accession_number = LookupTable()
    lut_accession_number.load(lut_accession_number_path)

    # common
    output_csv_path = os.path.join(output_path, 'file_crosswalk.csv')

    clean_output_directory = True
    if clean_output_directory:
            output_files = os.listdir(output_path)
            for output_file in output_files:
                os.remove(os.path.join(output_path, output_file))

    start_time = time.time()

    with open(output_csv_path, 'w') as output_csv:
        row_values = ['cleaned', 'original_file_path', 'cleaned_file_path', 'renamed_file_path',
            'PatientID', 'PatientName','PatientBirthDate', 'PatientSex', 'AccessionNumber', 'Modality', 'StudyDate', 'SOPInstanceUID', 'InstitutionName', 'StationName',
            'DeidPatientID', 'DeidPatientName', 'DeidPatientBirthDate', 'DeidPatientSex', 'DeidAccessionNumber', 'DeidModality' 'DeidStudyDate', 'DeidSOPInstanceUID', 'DeidInstitutionName', 'DeidStationName']
        row_text = ','.join(row_values)
        output_csv.write("%s\n" %row_text[:-1])

        for dicom_file_ids in deid_data(input_path, output_path, deid_path, config_file_path, 
                                     lut_patient_id, lut_accession_number):
            for (image, fields) in dicom_file_ids.items():
                file_tags = dump_file(fields['renamed_file_path'], ['PatientID',
                                                                    'PatientName',
                                                                    'PatientBirthDate',
                                                                    'PatientSex',
                                                                    'AccessionNumber',
                                                                    'Modality',
                                                                    'StudyDate',
                                                                    'SOPInstanceUID',
                                                                    'InstitutionName',
                                                                    'StationName'])
                row_values = get_values(fields, ['cleaned','original_file_path','cleaned_file_path','renamed_file_path', 'Modality',
                                                'PatientID','PatientName','PatientBirthDate','PatientSex','AccessionNumber','Modality','StudyDate','SOPInstanceUID','InstitutionName','StationName'])
                row_values += get_values(file_tags, ['PatientID','PatientName','PatientBirthDate','PatientSex','AccessionNumber','Modality','StudyDate','SOPInstanceUID','InstitutionName','StationName'])
                row_text = ','.join(row_values)
                output_csv.write("%s\n" %row_text)

    end_time = time.time()
    print("Elapsed time %s" %str(end_time - start_time))

    lut_patient_id.save(lut_patient_id_path)
    lut_accession_number.save(lut_accession_number_path)
