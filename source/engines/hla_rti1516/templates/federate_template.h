<DTIG_IMPORTS>
#include "DTIG>AMBASSADOR_HEADER"
#include <RTI/RTIambassador.h>
#include <memory>

#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>

#include <google/protobuf/message.h>
#include "dtig/return_value.pb.h"

#define READY_TO_RUN "ReadyToRun"

<DTIG_CLASSNAME>
HLAFederate

<DTIG_CONSTRUCTOR(PUBLIC)>
HLAFederate();

<DTIG_DESTRUCTOR(PUBLIC)>
virtual ~HLAFederate();

<DTIG_RUN>
void runFederate(const std::string& federateName, const std::string& fom, const std::string& address, uint32_t port);

<DTIG_MEMBER(PUBLIC)>
std::shared_ptr<DTIG>AMBASSADOR> fedamb;
std::auto_ptr<rti1516::RTIambassador> rtiamb;

<DTIG_MEMBER(PRIVATE)>
uint16_t mPort;
std::string mName;

int mClient = -1;
char mBuffer[1024] = {0};

DTIG_IF(DTIG_PARAMETERS)
rti1516::ObjectClassHandle mAttributeHandler;
std::map<std::string, rti1516::AttributeHandle> mAttributeHandlers;
DTIG_END_IF

DTIG_IF(DTIG_INPUTS)
rti1516::InteractionClassHandle mInputHandler;
std::map<rti1516::ParameterHandle, std::string> mInputHandlers;
DTIG_END_IF

DTIG_IF(DTIG_OUTPUTS)
rti1516::InteractionClassHandle mOutputHandler;
std::map<std::string, rti1516::ParameterHandle> mOutputHandlers;
DTIG_END_IF

<DTIG_METHOD(PRIVATE)>

std::wstring convertStringToWstring(const std::string& str);
rti1516::VariableLengthData toVariableLengthData(const char* s);

// ==============================
// Model specific calls
DTIG>CALLBACK(PUBLISH)
DTIG>CALLBACK(SUBSCRIBE)
DTIG>CALLBACK(INITIALIZE)
DTIG>CALLBACK(SET_PARAMETER)
DTIG>CALLBACK(GET_PARAMETER)
DTIG>CALLBACK(SET_INPUT)
DTIG>CALLBACK(GET_OUTPUT)

// ==============================
// Common calls
void waitForUser();
void enableTimePolicy();
void publishAndSubscribe();
void updateAttributeValues(rti1516::ObjectInstanceHandle objectHandle);
void sendInteraction();
void advanceTime(double timestep);
void deleteObject(rti1516::ObjectInstanceHandle objectHandle);
std::string getAttribute(const rti1516::AttributeHandle& handle) const;

rti1516::ObjectInstanceHandle registerObject();

dtig::MReturnValue SendMessage(const google::protobuf::Message& message);

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

<DTIG_CALLBACK(INITIALIZE)>
void InitializeHandles();

<DTIG_CALLBACK(PUBLISH)>
DTIG_IF(DTIG_PARAMETERS)
void SetupPublishers();
DTIG_ELSE
// No publishers
DTIG_END_IF

<DTIG_CALLBACK(SUBSCRIBE)>
DTIG_IF(DTIG_PARAMETERS)
void SetupSubscribers();
DTIG_ELSE
// No subscribers
DTIG_END_IF

<DTIG_CALLBACK(SET_INPUT)>
DTIG_IF(DTIG_INPUTS)
void SetInputs(const rti1516::InteractionClassHandle& interaction, const rti1516::ParameterHandleValueMap& parameterValues);
DTIG_ELSE
// No inputs
DTIG_END_IF

<DTIG_CALLBACK(GET_OUTPUT)>
DTIG_IF(DTIG_INPUTS)
void GetOutput();
DTIG_ELSE
// No outputs
DTIG_END_IF

<DTIG_CALLBACK(SET_PARAMETER)>
DTIG_IF(DTIG_PARAMETERS)
void SetParameters(const rti1516::ObjectInstanceHandle& object, const rti1516::AttributeHandleValueMap& attributes);
DTIG_ELSE
// No parameters to set
DTIG_END_IF

<DTIG_CALLBACK(GET_PARAMETER)>
DTIG_IF(DTIG_PARAMETERS)
void GetParameter(const ObjectInstanceHandle& handler);
DTIG_ELSE
// No parameters to get
DTIG_END_IF