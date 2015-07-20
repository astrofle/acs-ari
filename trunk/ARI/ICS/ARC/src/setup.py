from setuptools import setup, Command
import os

class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        os.system('rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')

#def readme():
    #with open('README.rst') as f:
        #return f.read()

setup(name='arcpy',
      version='0.1',
      description='Academic Radio Correlator control module',
      #url='http://github.com/storborg/funniest',
      #author='Flying Circus',
      #author_email='flyingcircus@example.com',
      license='MIT',
      packages=['arcpy'],
      zip_safe=False,
      install_requires=['corr', 'ValonSynth'],
      dependency_links=['', 'https://github.com/nrao/ValonSynth#egg=ValonSynth-1.0'],
      cmdclass={'clean':CleanCommand})
