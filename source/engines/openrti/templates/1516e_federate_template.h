<DTIG_IMPORTS>
#include "DTIG>AMBASSADOR_HEADER"
#include <RTI/RTIambassador.h>

#include <condition_variable>
#include <memory>
#include <mutex>

// TODO: This are platform specific
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>

#include <google/protobuf/any.h>

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

// Parameter handles
DTIG_FOR(DTIG_PARAMETERS)
rti1516::ObjectClassHandle mAttrDTIG_ITEM_NAME;
rti1516::ObjectInstanceHandle mPDTIG_ITEM_NAME;
std::map<std::string, rti1516::AttributeHandle> mPsDTIG_ITEM_NAME;
DTIG_END_FOR

// Input handles
DTIG_FOR(DTIG_INPUTS)
rti1516::InteractionClassHandle mIDTIG_ITEM_NAME;
std::map<rti1516::ParameterHandle, std::string> mIsDTIG_ITEM_NAME;
DTIG_END_FOR

// Output handles
DTIG_FOR(DTIG_OUTPUTS)
rti1516::InteractionClassHandle mODTIG_ITEM_NAME;
std::map<std::string, rti1516::ParameterHandle> mOsDTIG_ITEM_NAME;
DTIG_END_FOR

enum class State
{
  IDLE = 0,
  RUN = 1,
  STOP = 2
} mState;

std::mutex mMutex;
std::condition_variable mCv;

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

DTIG>CALLBACK(RUNCLIENT)

// ==============================
// Generated methods
// Parameters
DTIG_FOR(DTIG_PARAMETERS)
void getAttributeDTIG_ITEM_NAME();
void setAttributeDTIG_ITEM_NAME(const rti1516::AttributeHandleValueMap& handles);
std::string getHandleDTIG_ITEM_NAME(const rti1516::AttributeHandle& handle) const;
rti1516::AttributeHandleValueMap AttributeMapFromDTIG_ITEM_NAME(const google::protobuf::Any& anyMessage);
DTIG_END_FOR

// Inputs
DTIG_FOR(DTIG_INPUTS)
DTIG_TO_PROTO_MESSAGE(DTIG_ITEM_TYPE) ProtoInputFromDTIG_ITEM_NAME(const rti1516::ParameterHandleValueMap& handles);
DTIG_END_FOR

// Outpus
DTIG_FOR(DTIG_OUTPUTS)
rti1516::ParameterHandleValueMap ParameterMapFromDTIG_ITEM_NAME(const google::protobuf::Any& anyMessage);
DTIG_END_FOR

// ==============================
// Common calls
void waitForUser();
void enableTimePolicy();
void publishAndSubscribe();
void updateAttributeValues(rti1516::ObjectInstanceHandle objectHandle);
void sendInteraction();
void advanceTime(double timestep);

void registerObjects();
void deleteObjects();

std::vector<double> forceVector = {};

dtig::MReturnValue SendMessage(const google::protobuf::Message& message);

template<typename T>
rti1516::VariableLengthData toData(const T* s)
{
  rti1516::VariableLengthData variableLengthData;
  if (s)
    variableLengthData.setData(s, sizeof(T));

  return variableLengthData;
}

rti1516::VariableLengthData toData(std::string* s)
{
  rti1516::VariableLengthData variableLengthData;
  if (s)
    variableLengthData.setData(s->c_str(), s->size());

  return variableLengthData;
}

template<typename T>
T fromData(rti1516::VariableLengthData data)
{
  return *(T*)data.data();
}

<DTIG_CALLBACK(RUNCLIENT)>
bool RunModel();

<DTIG_CALLBACK(INITIALIZE)>
void InitializeHandles();

<DTIG_CALLBACK(PUBLISH)>
void SetupPublishers();

<DTIG_CALLBACK(SUBSCRIBE)>
void SetupSubscribers();

<DTIG_CALLBACK(SET_INPUT)>
void SetInputs(const rti1516::InteractionClassHandle& interaction, const rti1516::ParameterHandleValueMap& parameterValues);

<DTIG_CALLBACK(GET_OUTPUT)>
void GetOutput();

<DTIG_CALLBACK(SET_PARAMETER)>
void SetParameters(const rti1516::ObjectInstanceHandle& object, const rti1516::AttributeHandleValueMap& attributes);

<DTIG_CALLBACK(GET_PARAMETER)>
void GetParameter(const ObjectInstanceHandle& handler);