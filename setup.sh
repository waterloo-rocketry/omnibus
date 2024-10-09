echo "\n----- Upgrading pip -----"
pip install --upgrade pip || return
echo "\n----- Installing tools -----"
pip install wheel || return

# Install requirements
echo "\n----- Installing global requirements -----"
pip install -r requirements.txt || return
echo "\n----- Installing NI source requirements -----"
pip install -r sources/ni/requirements.txt || return
echo "\n----- Installing Parsley source requirements -----"
pip install -r sources/parsley/requirements.txt || return
echo "\n----- Installing Dashboard sink requirements -----"
pip install -r sinks/dashboard/requirements.txt || return
echo "\n----- Installing Interamap sink requirements -----"
pip install -r sinks/interamap/requirements.txt || return

# Install local libraries
echo "\n----- Installing Omnibus library -----"
pip install -e . || return
echo "\n----- Installing Parsley library -----"
git submodule update --init --recursive || return
pip install -e ./parsley || return

echo "\n----- Omnibus setup successfully -----"
