import os
import csv
import itertools


class LookupTable(object):
    def __init__(self):
        self.lut = {}

    def load(self, lut_path):
        with open(lut_path, 'r') as f:
            reader = csv.reader(f)
            for i, row in zip(itertools.count(), reader):
                if i == 0:
                    continue # skip header
                self.lut[row[0]] = row[1]
        return self.lut

    def save(self, lut_path, headers=['key', 'value']):
        with open(lut_path, 'w+') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for key in self.lut.keys():
                writer.writerow([key, self.lut[key]])
        return self.lut

    def look_up_value(self, lookup_key, fail=False, add=False, value_format='{}'):
        if lookup_key in self.lut:
            return self.lut[lookup_key]

        if fail:
            raise Exception('%s not found' %lookup_key)

        if add:
            lookup_value = value_format.format(len(self.lut))
            self.lut[lookup_key] = lookup_value
            return self.lut[lookup_key]

        return None

if __name__ == "__main__":
    lut_patient_id_path = os.path.abspath('f:\\data\\deid_config\\lut_patient_id.csv')
    lut_patient_id = LookupTable()
    lut_patient_id.load(lut_patient_id_path)

    lut_patient_id.look_up_value('999888', fail=False, add=True, value_format='p{:06d}')
    lut_patient_id.save(os.path.abspath('f:\\data\\deid_config\\lut_patient_id_test.csv'), ['patient_id', 'deid_patient_id'])
