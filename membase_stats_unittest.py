#
# Copyright 2009-2011 AppFirst, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 

#!/usr/bin/env python
# ./membase_stats_unittest.py

from membase_stats import MembaseStats
import unittest
import os

class MembaseStatsUnittest(unittest.TestCase):
    def setUp(self):
        print "set up"
        self.membase = MembaseStats()
    
    def tearDown(self):
        self.membase = None
        print "tear down"
        
    def test_before_work(self):
        self.assertEqual(self.membase.data_file_name, "/usr/share/appfirst/plugins/membase_stats_data", "wrong membase data file name")
        file = open(self.membase.data_file_name, 'r')
        expected_item_count = len(file.readlines())
        file.close()
        if os.path.exists(self.membase.data_file_name):
            self.membase.before_work()
            self.assertEqual(len(self.membase.prev_stats.keys()), expected_item_count, "no previous stats")
        
        local_path = "local_membase_test"
        my_key = "lalala"
        my_value = 1
        file = open(local_path, 'w')
        file.write("%s %s\n" % (my_key, my_value))
        file.close()
        tmp_file_name = self.membase.data_file_name
        self.membase.data_file_name = local_path
        self.membase.before_work()
        self.assertEqual(len(self.membase.prev_stats.keys()), 1 + expected_item_count, "key count error")
        self.assertTrue(self.membase.prev_stats.has_key(my_key), "key error")
        self.assertEqual(self.membase.prev_stats[my_key], my_value, "value error")
        os.remove(local_path)
        self.membase.data_file_name = tmp_file_name
        
    def test_after_work(self):
        local_path = "./local_membase_test"
        tmp_file_name = self.membase.data_file_name
        self.membase.data_file_name = local_path
        self.membase.prev_stats = {}
        
        for cnt in range(1, 100):
            self.membase.prev_stats[str(cnt)] = cnt
            
        self.membase.after_work()
        self.membase.prev_stats = {}
        self.membase.before_work()
        for cnt in range(1, 100):
            self.assertTrue(self.membase.prev_stats.has_key(str(cnt)), "key error")
            self.assertEqual(self.membase.prev_stats[str(cnt)], cnt, "value error")
        
        self.membase.data_file_name = tmp_file_name
        os.remove(local_path)
    
    def test_process_data(self):
        self.membase.d_stats = {}
        base = 10
        cnt = 0
        for key in self.membase.resource_name_mapping:
            self.membase.d_stats[key] = base + cnt
            self.membase.prev_stats[key] = base
            type = self.membase.resource_name_mapping[key]['type']
            name = self.membase.resource_name_mapping[key]['name']
            result = ""
            result = self.membase.process_data(key)
            print result
            expected = "%s=%s%s " % (name, self.membase.d_stats[key], self.membase.resource_name_mapping[key]['unit'])
            print expected 
            self.assertEqual(expected, result, "written error")
            if type == "cumulative":
                self.assertEqual(self.membase.d_stats[key], cnt, "processing error of cumulative data")
                self.assertEqual(self.membase.prev_stats[key], cnt + base, "assignning error %s %s" % (self.membase.prev_stats[key], cnt + base))
            else:
                self.assertEqual(self.membase.d_stats[key], cnt + base, "processing error of cumulative data")
            cnt = cnt + 1
        
        my_key = "lalala"
        my_value = 1
        self.membase.d_stats[my_key] = my_value
        result = self.membase.process_data(my_key)
        expected = "%s=%s " % (my_key, my_value)
        self.assertEqual(result, expected, "other data key error")
        
    def test_resident_ratio(self):
        expected = "%s=%s%s " % ('resident_item_ratio', 100, '%')
        self.membase.d_stats = {}
        result = self.membase.get_resident_ratio()
        self.assertEqual(expected, result, "don't test null data correctly")
        self.membase.d_stats['curr_items'] = 0
        result = self.membase.get_resident_ratio()
        self.assertEqual(expected, result, "don't test divide by 0 correctly")
        self.membase.d_stats['curr_items'] = 10000
        result = self.membase.get_resident_ratio()
        self.assertEqual(expected, result, "don't test null nominator correctly")
        self.membase.d_stats['ep_num_active_non_resident'] = 1000
        expected = "%s=%s%s " % ('resident_item_ratio', float(90), '%')
        result = self.membase.get_resident_ratio()
        self.assertEqual(expected, result, "get resident ratio wrong")
        
    def test_cache_miss_ratio(self):
        expected = "%s=%s%s " % ('cache_miss_ratio', 0, '%')
        self.membase.d_stats = {}
        result = self.membase.get_cache_miss_ratio()
        self.assertEqual(expected, result, "don't test null data correctly")
        self.membase.d_stats['get_hits'] = 0
        result = self.membase.get_cache_miss_ratio()
        self.assertEqual(expected, result, "don't test divide by 0 correctly")
        self.membase.d_stats['get_hits'] = 10000
        result = self.membase.get_cache_miss_ratio()
        self.assertEqual(expected, result, "don't test null nominator correctly")
        self.membase.d_stats['ep_bg_fetched'] = 1000
        expected = "%s=%s%s " % ('cache_miss_ratio', float(10), '%')
        result = self.membase.get_cache_miss_ratio()
        self.assertEqual(expected, result, "get cache ratio wrong")
    
    def test_replica_resident_ratio(self):
        expected = "%s=%s%s " % ('replica_resident_ratio', 100, '%')
        self.membase.d_stats = {}
        result = self.membase.get_replica_resident_ratio()
        self.assertEqual(expected, result, "don't test null data correctly")
        self.membase.d_stats['curr_items_tot'] = 0
        result = self.membase.get_replica_resident_ratio()
        self.assertEqual(expected, result, "don't test null data correctly")
        self.membase.d_stats['curr_items_tot'] = 10000
        result = self.membase.get_replica_resident_ratio()
        self.assertEqual(expected, result, "don't test null data correctly")
        self.membase.d_stats['ep_num_non_resident'] = 6000
        result = self.membase.get_replica_resident_ratio()
        self.assertEqual(expected, result, "don't test wrong status correctly")
        self.membase.d_stats['ep_num_active_non_resident'] = 4000
        result = self.membase.get_replica_resident_ratio()
        self.assertEqual(expected, result, "don't test wrong status correctly")
        self.membase.d_stats['curr_items'] = 11000
        result = self.membase.get_replica_resident_ratio()
        self.assertEqual(expected, result, "don't test wrong status correctly")
        self.membase.d_stats['curr_items'] = 5000
        expected = "%s=%s%s " % ('replica_resident_ratio', float(60), '%')
        result = self.membase.get_replica_resident_ratio()
        self.assertEqual(expected, result, "get replica ratio wrong")
        
    def test_main(self):
        if os.path.exists(self.membase.data_file_name) == False:
            self.membase.main()
        self.assertTrue(os.path.exists(self.membase.data_file_name), "program couldn't run correctly")
        prev_stats = {}
        for key in self.membase.prev_stats:
            prev_stats[key] = self.membase.prev_stats[key]
        self.membase.main()
        for key in self.membase.prev_stats:
            if self.membase.resource_name_mapping.has_key(key) and \
                self.membase.resource_name_mapping[key]['type'] == 'cumulative':
                self.assertEqual(self.membase.d_stats[key], self.membase.prev_stats[key] - prev_stats[key], "calculation error")
            
    def test_get_status(self):
        self.membase.get_status()
        for key in self.membase.resource_name_mapping:
            self.assertTrue(self.membase.d_stats.has_key(key), "not getting raw status correctly")


if __name__ == '__main__':
    unittest.main()