import java.io.*;

import dtig.*;
import com.google.protobuf.*;

public class Test {

  public static void main(String args[])
  {
    dtig.MAdvance msg = dtig.MAdvance.newBuilder()
        .setStepSize(dtig.MStep.newBuilder()
            .setStep(dtig.MNumber64.newBuilder()
                .setFvalue(dtig.MF64.newBuilder()
                    .setValue(0.05))
            )
        ).build();

    System.out.println("Simple message creation");
    dtig.MNumber64 number = msg.getStepSize().getStep();
    if (number.hasFvalue())
      System.out.println(number.getFvalue().getValue());

    System.out.println(msg.toString());

    System.out.println("A more complicated message creation");
    dtig.MValues.Builder inputs = dtig.MValues.newBuilder();
    // Add identifiers
    dtig.MNames names = dtig.MNames.newBuilder()
      .addNames("h")
      .addNames("g")
      .addNames("v")
      .build();

    dtig.MIdentifiers identifiers = dtig.MIdentifiers.newBuilder()
      .setNames(names)
      .build();

    inputs.setIdentifiers(
      dtig.MIdentifiers.newBuilder()
        .setNames(names));

    // Add valueS
    inputs.addValues(com.google.protobuf.Any.pack(
      dtig.MF64.newBuilder()
        .setValue(0.8)
        .build()
    ));
    inputs.addValues(com.google.protobuf.Any.pack(
      dtig.MF64.newBuilder()
        .setValue(0.9)
        .build()
    ));
    inputs.addValues(com.google.protobuf.Any.pack(
      dtig.MF64.newBuilder()
        .setValue(1.0)
        .build()
    ));

    dtig.MInput input = dtig.MInput.newBuilder()
      .setInputs(inputs.build())
      .build();

    System.out.println(input.toString());

    System.out.println("Unpacking values");
    for (com.google.protobuf.Any item : input.getInputs().getValuesList())
    {
      try
      {
        String clazzName = item.getTypeUrl().split("/")[1];
        System.out.printf("Trying to unpack %s %n", clazzName);
        Class<com.google.protobuf.Message> clazz = (Class<com.google.protobuf.Message>) Class.forName(clazzName);
        System.out.println(item.unpack(clazz).toString());
      } catch (InvalidProtocolBufferException e) {
        System.out.println("Could not unpack value");
      } catch (ClassNotFoundException e) {
        System.out.println("Could not find class");
      }
    }

    var start = dtig.MStart.newBuilder()
      .setStartTime(dtig.MNumber32.newBuilder()
        .setFvalue(dtig.MF32.newBuilder()
          .setValue(0.05f))).build();

    float startTime = 0.0f;
    float stopTime = 0.0f;
    float stepTime = 0.0f;

    if (start.hasStepSize())
    {
    }

    if (start.hasStartTime())
    {
      System.out.println(FromNumber32(start.getStartTime()).toString());
    }
  }

  public static <T> T FromNumber32(dtig.MNumber32 number)
  {
    if (number.hasFvalue())
      return (T) (Float) number.getFvalue().getValue();
    else if (number.hasIvalue())
      return (T) (Integer) number.getIvalue().getValue();
    else if (number.hasUvalue())
      return (T) (Integer) number.getUvalue().getValue();

    return null;
  }
}
