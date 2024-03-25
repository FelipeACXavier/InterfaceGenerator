# InterfaceGenerator


## How to build

- CPP: protoc -I=$SRC_DIR --cpp_out=$DST_DIR $SRC_DIR/addressbook.proto
- Python: protoc -I=$SRC_DIR --python_out=$DST_DIR $SRC_DIR/addressbook.proto
- .NET: protoc -I=$SRC_DIR --csharp_out=$DST_DIR $SRC_DIR/addressbook.proto
- Java: protoc -I=$SRC_DIR --java_out=$DST_DIR $SRC_DIR/addressbook.proto