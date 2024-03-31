@imports
#include "@ambassador_header"
#include <RTI/RTIambassador.h>
#include <memory>

#define READY_TO_RUN "ReadyToRun"

@classname
HLAFederate

@constructor
HLAFederate();

@destructor
virtual ~HLAFederate();

@run
void runFederate(const std::string& federateName, const std::string& fom, const std::string& address);

@member(public)
std::shared_ptr<@ambassador> fedamb;
std::shared_ptr<rti1516::RTIambassador> rtiamb;

@member(private)
std::string mName;

rti1516::AttributeHandle aaHandle;
rti1516::AttributeHandle abHandle;
rti1516::AttributeHandle acHandle;
rti1516::ObjectClassHandle aHandle;

rti1516::ParameterHandle xaHandle;
rti1516::ParameterHandle xbHandle;
rti1516::InteractionClassHandle xHandle;

@method(private)
std::wstring convertStringToWstring(const std::string& str);
rti1516::VariableLengthData toVariableLengthData(const char* s);

void initializeHandles();
void waitForUser();
void enableTimePolicy();
void publishAndSubscribe();
void updateAttributeValues(rti1516::ObjectInstanceHandle objectHandle);
void sendInteraction();
void advanceTime(double timestep);
void deleteObject(rti1516::ObjectInstanceHandle objectHandle);

rti1516::ObjectInstanceHandle registerObject();

double getLbts();