<DTIG_IMPORTS>
#include <RTI/NullFederateAmbassador.h>
#include <functional>

using namespace rti1516;

<DTIG_CLASSNAME>
HLAAmbassador

<DTIG_INHERIT(PUBLIC)>
NullFederateAmbassador

<DTIG_CONSTRUCTOR(PUBLIC)>
HLAAmbassador();

<DTIG_DESTRUCTOR(PUBLIC)>
virtual ~HLAAmbassador() throw();

<DTIG_METHOD(PUBLIC)>
virtual void synchronizationPointRegistrationSucceeded(std::wstring const& label) throw(FederateInternalError);

virtual void synchronizationPointRegistrationFailed(std::wstring const& label, SynchronizationFailureReason reason) throw(FederateInternalError);

virtual void announceSynchronizationPoint(std::wstring const& label, VariableLengthData const& theUserSuppliedTag) throw(FederateInternalError);

virtual void federationSynchronized(std::wstring const& label) throw(FederateInternalError);

virtual void timeRegulationEnabled(LogicalTime const& theFederateTime) throw(InvalidLogicalTime,
                                                                              NoRequestToEnableTimeRegulationWasPending,
                                                                              FederateInternalError);

virtual void timeConstrainedEnabled(LogicalTime const& theFederateTime) throw(InvalidLogicalTime,
                                                                              NoRequestToEnableTimeConstrainedWasPending,
                                                                              FederateInternalError);

virtual void timeAdvanceGrant(LogicalTime const& theTime) throw(InvalidLogicalTime,
                                                                JoinedFederateIsNotInTimeAdvancingState,
                                                                FederateInternalError);

virtual void discoverObjectInstance(ObjectInstanceHandle theObject,
                                    ObjectClassHandle theObjectClass,
                                    std::wstring const& theObjectInstanceName) throw(CouldNotDiscover,
                                                                                      ObjectClassNotKnown,
                                                                                      FederateInternalError);

virtual void reflectAttributeValues(ObjectInstanceHandle theObject,
                                    AttributeHandleValueMap const& theAttributeValues,
                                    VariableLengthData const& theUserSuppliedTag,
                                    OrderType sentOrder,
                                    TransportationType theType) throw(ObjectInstanceNotKnown,
                                                                      AttributeNotRecognized,
                                                                      AttributeNotSubscribed,
                                                                      FederateInternalError);

virtual void reflectAttributeValues(ObjectInstanceHandle theObject,
                                    AttributeHandleValueMap const& theAttributeValues,
                                    VariableLengthData const& theUserSuppliedTag,
                                    OrderType sentOrder,
                                    TransportationType theType,
                                    RegionHandleSet const& theSentRegionHandleSet) throw(ObjectInstanceNotKnown,
                                                                                          AttributeNotRecognized,
                                                                                          AttributeNotSubscribed,
                                                                                          FederateInternalError);

virtual void reflectAttributeValues(ObjectInstanceHandle theObject,
                                    AttributeHandleValueMap const& theAttributeValues,
                                    VariableLengthData const& theUserSuppliedTag,
                                    OrderType sentOrder,
                                    TransportationType theType,
                                    LogicalTime const& theTime,
                                    OrderType receivedOrder) throw(ObjectInstanceNotKnown,
                                                                    AttributeNotRecognized,
                                                                    AttributeNotSubscribed,
                                                                    FederateInternalError);

virtual void receiveInteraction(InteractionClassHandle theInteraction, ParameterHandleValueMap const& theParameterValues, VariableLengthData const& theUserSuppliedTag, OrderType sentOrder, TransportationType theType) throw(InteractionClassNotRecognized, InteractionParameterNotRecognized, InteractionClassNotSubscribed, FederateInternalError);
virtual void receiveInteraction(InteractionClassHandle theInteraction, ParameterHandleValueMap const& theParameterValues, VariableLengthData const& theUserSuppliedTag, OrderType sentOrder, TransportationType theType, RegionHandleSet const& theSentRegionHandleSet) throw(InteractionClassNotRecognized, InteractionParameterNotRecognized, InteractionClassNotSubscribed, FederateInternalError);
virtual void receiveInteraction(InteractionClassHandle theInteraction, ParameterHandleValueMap const& theParameterValues, VariableLengthData const& theUserSuppliedTag, OrderType sentOrder, TransportationType theType, LogicalTime const& theTime, OrderType receivedOrder) throw(InteractionClassNotRecognized, InteractionParameterNotRecognized, InteractionClassNotSubscribed, FederateInternalError);
virtual void receiveInteraction(InteractionClassHandle theInteraction, ParameterHandleValueMap const& theParameterValues, VariableLengthData const& theUserSuppliedTag, OrderType sentOrder, TransportationType theType, LogicalTime const& theTime, OrderType receivedOrder, RegionHandleSet const& theSentRegionHandleSet) throw(InteractionClassNotRecognized, InteractionParameterNotRecognized, InteractionClassNotSubscribed, FederateInternalError);
virtual void receiveInteraction(InteractionClassHandle theInteraction, ParameterHandleValueMap const& theParameterValues, VariableLengthData const& theUserSuppliedTag, OrderType sentOrder, TransportationType theType, LogicalTime const& theTime, OrderType receivedOrder, MessageRetractionHandle theHandle) throw(InteractionClassNotRecognized, InteractionParameterNotRecognized, InteractionClassNotSubscribed, InvalidLogicalTime, FederateInternalError);
virtual void receiveInteraction(InteractionClassHandle theInteraction, ParameterHandleValueMap const& theParameterValues, VariableLengthData const& theUserSuppliedTag, OrderType sentOrder, TransportationType theType, LogicalTime const& theTime, OrderType receivedOrder, MessageRetractionHandle theHandle, RegionHandleSet const& theSentRegionHandleSet) throw(InteractionClassNotRecognized, InteractionParameterNotRecognized, InteractionClassNotSubscribed, InvalidLogicalTime, FederateInternalError);

virtual void removeObjectInstance(ObjectInstanceHandle theObject, VariableLengthData const& theUserSuppliedTag, OrderType sentOrder) throw(ObjectInstanceNotKnown, FederateInternalError);

virtual void removeObjectInstance(ObjectInstanceHandle theObject, VariableLengthData const& theUserSuppliedTag, OrderType sentOrder, LogicalTime const& theTime, OrderType receivedOrder) throw(ObjectInstanceNotKnown, FederateInternalError);
virtual void removeObjectInstance(ObjectInstanceHandle theObject, VariableLengthData const& theUserSuppliedTag, OrderType sentOrder, LogicalTime const& theTime, OrderType receivedOrder, MessageRetractionHandle theHandle) throw(ObjectInstanceNotKnown, InvalidLogicalTime, FederateInternalError);

<DTIG_METHOD(PRIVATE)>
double convertTime(rti1516::LogicalTime const& theTime);
std::wstring variableLengthDataToWstring(const rti1516::VariableLengthData& variableLengthData);

<DTIG_MEMBER(PUBLIC)>
double federateTime;
double federateLookahead;

bool isRegulating;
bool isConstrained;
bool isAdvancing;
bool isAnnounced;
bool isReadyToRun;

std::function<void(rti1516::ObjectInstanceHandle theObject,
  const rti1516::AttributeHandleValueMap& theAttributeValues)> attributeReceived;
std::function<void(rti1516::InteractionClassHandle theInteraction,
  const rti1516::ParameterHandleValueMap& theParameterValues)> interactionReceived;