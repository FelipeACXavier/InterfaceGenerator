# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protobuf/values.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from protobuf import identifiers_pb2 as protobuf_dot_identifiers__pb2
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='protobuf/values.proto',
  package='dti',
  syntax='proto3',
  serialized_options=_b('P\001'),
  serialized_pb=_b('\n\x15protobuf/values.proto\x12\x03\x64ti\x1a\x1aprotobuf/identifiers.proto\x1a\x19google/protobuf/any.proto\"W\n\x07MValues\x12&\n\x0bidentifiers\x18\x01 \x01(\x0b\x32\x11.dti.MIdentifiers\x12$\n\x06values\x18\n \x03(\x0b\x32\x14.google.protobuf.AnyB\x02P\x01\x62\x06proto3')
  ,
  dependencies=[protobuf_dot_identifiers__pb2.DESCRIPTOR,google_dot_protobuf_dot_any__pb2.DESCRIPTOR,])




_MVALUES = _descriptor.Descriptor(
  name='MValues',
  full_name='dti.MValues',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='identifiers', full_name='dti.MValues.identifiers', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='values', full_name='dti.MValues.values', index=1,
      number=10, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
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
  serialized_start=85,
  serialized_end=172,
)

_MVALUES.fields_by_name['identifiers'].message_type = protobuf_dot_identifiers__pb2._MIDENTIFIERS
_MVALUES.fields_by_name['values'].message_type = google_dot_protobuf_dot_any__pb2._ANY
DESCRIPTOR.message_types_by_name['MValues'] = _MVALUES
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

MValues = _reflection.GeneratedProtocolMessageType('MValues', (_message.Message,), dict(
  DESCRIPTOR = _MVALUES,
  __module__ = 'protobuf.values_pb2'
  # @@protoc_insertion_point(class_scope:dti.MValues)
  ))
_sym_db.RegisterMessage(MValues)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
