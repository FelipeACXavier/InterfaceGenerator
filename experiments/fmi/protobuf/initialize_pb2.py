# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protobuf/initialize.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from protobuf import utils_pb2 as protobuf_dot_utils__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='protobuf/initialize.proto',
  package='dti',
  syntax='proto3',
  serialized_options=_b('P\001'),
  serialized_pb=_b('\n\x19protobuf/initialize.proto\x12\x03\x64ti\x1a\x14protobuf/utils.proto\"\x9c\x01\n\x0bMInitialize\x12%\n\x0fsimulation_name\x18\n \x01(\x0b\x32\x0c.dti.MString\x12 \n\nmodel_name\x18\x14 \x01(\x0b\x32\x0c.dti.MString\x12!\n\x0b\x63onfig_file\x18\x1e \x01(\x0b\x32\x0c.dti.MString\x12!\n\x0c\x63onfig_bytes\x18# \x01(\x0b\x32\x0b.dti.MBytesB\x02P\x01\x62\x06proto3')
  ,
  dependencies=[protobuf_dot_utils__pb2.DESCRIPTOR,])




_MINITIALIZE = _descriptor.Descriptor(
  name='MInitialize',
  full_name='dti.MInitialize',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='simulation_name', full_name='dti.MInitialize.simulation_name', index=0,
      number=10, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='model_name', full_name='dti.MInitialize.model_name', index=1,
      number=20, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='config_file', full_name='dti.MInitialize.config_file', index=2,
      number=30, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='config_bytes', full_name='dti.MInitialize.config_bytes', index=3,
      number=35, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=57,
  serialized_end=213,
)

_MINITIALIZE.fields_by_name['simulation_name'].message_type = protobuf_dot_utils__pb2._MSTRING
_MINITIALIZE.fields_by_name['model_name'].message_type = protobuf_dot_utils__pb2._MSTRING
_MINITIALIZE.fields_by_name['config_file'].message_type = protobuf_dot_utils__pb2._MSTRING
_MINITIALIZE.fields_by_name['config_bytes'].message_type = protobuf_dot_utils__pb2._MBYTES
DESCRIPTOR.message_types_by_name['MInitialize'] = _MINITIALIZE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

MInitialize = _reflection.GeneratedProtocolMessageType('MInitialize', (_message.Message,), dict(
  DESCRIPTOR = _MINITIALIZE,
  __module__ = 'protobuf.initialize_pb2'
  # @@protoc_insertion_point(class_scope:dti.MInitialize)
  ))
_sym_db.RegisterMessage(MInitialize)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
