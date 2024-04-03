package dtig;

import java.util.Arrays;
import java.io.IOException;

import com.google.protobuf.Any;
import com.google.protobuf.Message;

public class Helpers {
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
