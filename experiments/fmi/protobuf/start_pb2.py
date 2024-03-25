# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protobuf/start.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from protobuf import step_pb2 as protobuf_dot_step__pb2
from protobuf import utils_pb2 as protobuf_dot_utils__pb2
from protobuf import run_mode_pb2 as protobuf_dot_run__mode__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='protobuf/start.proto',
  package='dti',
  syntax='proto3',
  serialized_options=_b('P\001'),
  serialized_pb=_b('\n\x14protobuf/start.proto\x12\x03\x64ti\x1a\x13protobuf/step.proto\x1a\x14protobuf/utils.proto\x1a\x17protobuf/run_mode.proto\"\x93\x01\n\x06MStart\x12\"\n\nstart_time\x18\x01 \x01(\x0b\x32\x0e.dti.MNumber32\x12!\n\tstop_time\x18\x02 \x01(\x0b\x32\x0e.dti.MNumber32\x12\x1d\n\tstep_size\x18\x03 \x01(\x0b\x32\n.dti.MStep\x12#\n\x08run_mode\x18\n \x01(\x0e\x32\x11.dti.Run.ERunModeB\x02P\x01\x62\x06proto3')
  ,
  dependencies=[protobuf_dot_step__pb2.DESCRIPTOR,protobuf_dot_utils__pb2.DESCRIPTOR,protobuf_dot_run__mode__pb2.DESCRIPTOR,])




_MSTART = _descriptor.Descriptor(
  name='MStart',
  full_name='dti.MStart',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='start_time', full_name='dti.MStart.start_time', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='stop_time', full_name='dti.MStart.stop_time', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='step_size', full_name='dti.MStart.step_size', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='run_mode', full_name='dti.MStart.run_mode', index=3,
      number=10, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
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
  serialized_start=98,
  serialized_end=245,
)

_MSTART.fields_by_name['start_time'].message_type = protobuf_dot_utils__pb2._MNUMBER32
_MSTART.fields_by_name['stop_time'].message_type = protobuf_dot_utils__pb2._MNUMBER32
_MSTART.fields_by_name['step_size'].message_type = protobuf_dot_step__pb2._MSTEP
_MSTART.fields_by_name['run_mode'].enum_type = protobuf_dot_run__mode__pb2._ERUNMODE
DESCRIPTOR.message_types_by_name['MStart'] = _MSTART
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

MStart = _reflection.GeneratedProtocolMessageType('MStart', (_message.Message,), dict(
  DESCRIPTOR = _MSTART,
  __module__ = 'protobuf.start_pb2'
  # @@protoc_insertion_point(class_scope:dti.MStart)
  ))
_sym_db.RegisterMessage(MStart)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
