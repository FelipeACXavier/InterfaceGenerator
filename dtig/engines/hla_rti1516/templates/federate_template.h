// @imports
#include "// @>ambassador_header"
#include <RTI/RTIambassador.h>
#include <memory>

#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>

#include <google/protobuf/message.h>
#include "protobuf/return_value.pb.h"

#define READY_TO_RUN "ReadyToRun"

// @classname
HLAFederate

// @constructor(public)
HLAFederate();

// @destructor(public)
virtual ~HLAFederate();

// @run
void runFederate(std::string federateName, std::string fom, std::string address, uint32_t port);

// @member(public)
std::shared_ptr<//@>ambassador> fedamb;
std::auto_ptr<rti1516::RTIambassador> rtiamb;

// @member(private)
uint16_t mPort;
std::string mName;

int mClient = -1;
char mBuffer[1024] = {0};

// @>callback(member)

// @method(private)
std::wstring convertStringToWstring(const std::string& str);
rti1516::VariableLengthData toVariableLengthData(const char* s);

// @>callback(publish)
// @>callback(subscribe)
// @>callback(initialize)
// @>callback(setparameter)
// @>callback(getparameter)
// @>callback(setinput)
// @>callback(getoutput)

void waitForUser();
void enableTimePolicy();
void publishAndSubscribe();
void updateAttributeValues(rti1516::ObjectInstanceHandle objectHandle);
void sendInteraction();
void advanceTime(double timestep);
void deleteObject(rti1516::ObjectInstanceHandle objectHandle);

rti1516::ObjectInstanceHandle registerObject();

dti::MReturnValue SendMessage(const google::protobuf::Message& message);

template<typename T>
rti1516::VariableLengthData toData(T* s)
{
  rti1516::VariableLengthData variableLengthData;
  if (s)
    variableLengthData.setData(s, sizeof(T));

  return variableLengthData;
}

rti1516::VariableLengthData toData(char* s)
{
  rti1516::VariableLengthData variableLengthData;
  if (s)
    variableLengthData.setData(s, strlen(s));

  return variableLengthData;
}

template<typename T>
T fromData(rti1516::VariableLengthData data)
{
  return *(T*)data.data();
}