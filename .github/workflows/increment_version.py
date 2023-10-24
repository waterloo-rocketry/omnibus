import os

version_file = 'omnibus/release_info.py'
with open(version_file, 'r+') as f:
    content = f.read()
    version_line = next(line for line in content.split('\n') if 'version' in line)
    version_str = version_line.split('=')[-1].strip().strip("'")
    major, minor, patch = map(int, version_str.split('.'))
    new_version = f"{major + 1}.0.0"
    new_content = content.replace(version_line, version_line.replace(version_str, new_version))
    f.seek(0)
    f.write(new_content)
    f.truncate()
print(f"::set-output name=new_version::{new_version}")
