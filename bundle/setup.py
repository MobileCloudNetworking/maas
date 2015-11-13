from setuptools import setup

setup(
    name='MaaSServiceOrchestrator',
    version='3.1',
    packages=['core', 'adapters', 'test', 'util', 'wsgi', 'model', 'services', 'interfaces', 'clients', 'emm_exceptions'],
#    install_requires=[
#	'python-heatclient==0.8.0',
#        'python-novaclient==2.30.0',
#        'python-ceilometerclient',
#        'python-neutronclient==3.1.0',
#        'python-novaclient==2.30.0',
#        'bottle==0.12.8',
#	'SQLAlchemy==0.9.8',
#    ],
    # test_suite="test",
    url='',
    license='',
    author='Giuseppe Carella',
    author_email='giuseppe.a.carella@tu-berlin.de',
    description='MaaS Service Orchestrator',
)
