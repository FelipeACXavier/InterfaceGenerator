# Digital Twin Interface Generator

Digital Twin Interface Generator (DTIG) is a library that helps with the creation of interfaces for digital twins and co-simulation.
DTIG is currently developed in python due to easy of use and no performance requirements.

## <a name="setup"></a> Using DTIG
To use the DTIG, simply create a model description in one of the supported engines and run the DTIG tool.
If the desired engine is not yet available, feel free to expand DTIG with it.
Follow the steps in [development](#development)

```bash
dtig -c <model.json>
```

## <a name="development"></a> Developing DTIG

To start developing with the DTIG:
```bash
# Clone this code to your preferred directory
git clone https://github.com/FelipeACXavier/InterfaceGenerator.git <your folder>

# Change to the cloned directory
cd <your folder>

# Create a new virtual environment
python3 -p venv env

# Activate the environment
source env/bin/activate

# Setup the project
# This will install all the necessary dependencies and setup the import paths
pip install -e .
```

Now you only need to update the library with the tool specific generation.
The DTIG library provides most of the necessary tools and libraries 

## How to build

- CPP: protoc -I=$SRC_DIR --cpp_out=$DST_DIR $SRC_DIR/addressbook.proto
- Python: protoc -I=$SRC_DIR --python_out=$DST_DIR $SRC_DIR/addressbook.proto
- .NET: protoc -I=$SRC_DIR --csharp_out=$DST_DIR $SRC_DIR/addressbook.proto
- Java: protoc -I=$SRC_DIR --java_out=$DST_DIR $SRC_DIR/addressbook.proto
- Matlab: 
  - Get jar from mvn: https://repo1.maven.org/maven2/com/google/protobuf/protobuf-java/3.20.3/protobuf-java-3.20.3.jar
  - From source dir: protoc -I=./ --java_out=experiments/matlab/ protobuf/*.proto
  - Make sure to use the same javac version as matlab
  - From matlab folder: javac -d build/ -cp protobuf-java-3.20.3.jar protobuf/*.java
  - Create jar: (cd build/ && jar cvf dtig.jar protobuf)


# TODO: 
## Generate necessary protobuf
- Check if protoc is installed
- Call protoc in known folder

## Formalize
### Usage decorators
@callback(name)
@imports
@constructor
@destructor
@run

### Development decorators
@parse(name)
@messagehandler
@imports
@state
@constructor
@destructor
@run
@main
@method

# Rules

- Servers must follow the common representation state machine when applicable. Jumps between states is valid as long as the correct state is available through the MGetStatus call
- MAdvance should be made blocking whenever possible in order to avoid polling the state. If that is not the case, the option "synchronous" should be set to false in the configuration file
- 