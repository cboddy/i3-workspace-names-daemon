from setuptools import setup


with open('README.md') as f:
    long_description = f.read()

setup(name='i3-workspace-names-daemon',
      version='0.10.0',
      description='Dynamically update the name of each i3wm workspace using font-awesome icons or the names of applications running in each workspace.',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/cboddy/i3-workspace-names-daemon',
      license='MIT',
      zip_safe=False,
      py_modules=['i3_workspace_names_daemon', 'fa_icons'],
      install_requires=["i3ipc"],
      author='Chris Boddy',
      author_email='chris@boddy.im',
      entry_points={
          'console_scripts': [
              'i3-workspace-names-daemon=i3_workspace_names_daemon:main'
          ]
      }
      )
