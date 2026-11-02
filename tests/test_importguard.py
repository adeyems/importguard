import contextlib
import csv
import io
import json
import unittest
from importguard import check, load_rows, validate_schema, main
S={'version':1,'fields':{'id':{'type':'integer','required':True},'active':{'type':'boolean','required':False}}}
class ValidationTest(unittest.TestCase):
    def test_json_types(self):
        result=check(load_rows('[{"id":true},{"id":2,"active":1},{}]','json'),S,'json')
        self.assertEqual(result['invalid_rows'],3)
        self.assertEqual([e['code'] for e in result['errors']],['type','type','required'])
    def test_csv_scalars(self):
        result=check(load_rows('id,active\n1,true\n02,false\n3,\n','csv'),S,'csv')
        self.assertEqual(result['errors'],[{'row':2,'field':'id','code':'type','expected':'integer'}])
    def test_malformed(self):
        for text in ['id,id\n1,2','id\n1,2','id\n"unterminated']:
            with self.assertRaises((ValueError,csv.Error)):load_rows(text,'csv')
        for text in ['{}','[1]','[{"id":1,"id":2}]','[NaN]']:
            with self.assertRaises(ValueError):load_rows(text,'json')
        with self.assertRaises(ValueError):validate_schema({'version':True,'fields':S['fields']})
    def test_diagnostic_bound(self):
        report=check([{}]*1001,S,'json')
        self.assertEqual(report['error_count'],1001)
        self.assertEqual(len(report['errors']),1000)
        self.assertTrue(report['errors_truncated'])
    def test_real_cli(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['examples/schema.json','examples/rows.csv','--format','csv']),1)
        self.assertEqual(json.loads(out.getvalue())['invalid_rows'],2)
        self.assertNotIn('wrong',out.getvalue())
    def test_optional_and_empty(self):
        self.assertTrue(check([{'id':1,'extra':'allowed','active':None}],S,'json')['valid'])
        self.assertTrue(check([],S,'json')['valid'])
    def test_input_limits_and_multiline_csv(self):
        rows=load_rows('id,active\n1,true\n','csv')
        self.assertEqual(rows[0]['id'],'1')
        self.assertEqual(load_rows('name\n"two\nlines"\n','csv')[0]['name'],'two\nlines')
        with self.assertRaises(ValueError):load_rows(json.dumps([{}]*10001),'json')
        import tempfile
        from pathlib import Path
        from importguard import read_text
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'large.json';path.write_bytes(b' '*(2*1024*1024+1))
            with self.assertRaises(ValueError):read_text(path)
    def test_cli_failure_does_not_echo_input(self):
        with contextlib.redirect_stdout(io.StringIO()) as out,contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(main(['examples/schema.json','does-not-exist','--format','json']),2)
        self.assertEqual(out.getvalue(),'')
        self.assertIn('error',json.loads(err.getvalue()))
