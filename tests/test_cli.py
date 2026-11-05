import os
import subprocess
import sys
import unittest


class CliTests(unittest.TestCase):
    def run_cli(self,*args,stdin=None):
        env=dict(os.environ)
        env.pop('OPENAI_API_KEY',None)
        return subprocess.run([sys.executable,'-m','emporio',*args],input=stdin,
                              text=True,capture_output=True,encoding='utf-8',env=env)

    def test_demo_single_message_no_key(self):
        result=self.run_cli('--mode','demo','--message','What is the store address?')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('3200',result.stdout)
        self.assertIn('DEMO',result.stdout)

    def test_missing_key_is_actionable(self):
        result=self.run_cli('--mode','openai','--message','hello')
        self.assertEqual(result.returncode,2)
        self.assertIn('OPENAI_API_KEY',result.stderr)
        self.assertNotIn('Traceback',result.stderr)

    def test_invalid_customer_id_rejected(self):
        result=self.run_cli('--mode','demo','--customer-id','0','--message','hello')
        self.assertEqual(result.returncode,2)

    def test_interactive_reset_and_exit(self):
        result=self.run_cli('--mode','demo',stdin='hello\n/reset\n/quit\n')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('cleared',result.stdout)

    def test_huge_customer_id_rejected(self):
        result=self.run_cli('--mode','demo','--customer-id',str(10**30),'--message','order 1')
        self.assertEqual(result.returncode,2)
        self.assertNotIn('Traceback',result.stderr)


if __name__=='__main__': unittest.main()
