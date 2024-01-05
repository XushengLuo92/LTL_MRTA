from setuptools import setup, find_packages

setup(
    name='mrta',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'backlog==2.0.4',
        'gurobipy==10.0.2',
        'matplotlib==3.8.1',
        'networkx==3.1',
        'numpy==1.25.2',
        'scipy==1.11.4',
        'sympy==1.12',
        'termcolor==2.4.0',
    ],
    author='Xusheng Luo',
    author_email='xusheng.luo2@gmail.com',
    description='Cource code for the paper "Temporal Logic Task Allocation in Heterogeneous Multi-Robot Systems"',
    license='MIT',
    url='https://github.com/XushengLuo92/LTL_MRTA',
)