package dtig;

import dtig.MDTMessage;
import dtig.MReturnValue;

import java.util.Arrays;
import java.io.IOException;

import com.google.protobuf.Any;
import com.google.protobuf.Message;

public class Helpers {
  public static dtig.MDTMessage parseFrom(byte[] data) throws IOException {
    return dtig.MDTMessage.parseFrom(data);
  }

  public static dtig.MReturnValue parseReturn(byte[] data) throws IOException {
    return dtig.MReturnValue.parseFrom(data);
  }

  public static byte[] toByteArray(dtig.MReturnValue.Builder message) {
    return message.build().toByteArray();
  }

  public static com.google.protobuf.Any pack(com.google.protobuf.Message.Builder message) {
    return com.google.protobuf.Any.pack(message.build());
  }

  public static com.google.protobuf.Message.Builder unpack(com.google.protobuf.Any message) {
    try {
      String clazzName = message.getTypeUrl().split("/")[1];
      @SuppressWarnings("unchecked")
      Class<com.google.protobuf.Message> clazz = (Class<com.google.protobuf.Message>) Class.forName(clazzName);
      return message.unpack(clazz).toBuilder();
    } catch (Exception e) {
      return null;
    }
  }
}
