from setuptools import setup

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
      dependency_links=['', 'https://github.com/nrao/ValonSynth#egg=ValonSynth-1.0'])
