# API Tests

The following sections list all special conditions when checking an AAS REST API.
Please note, that in case of checking responses, the conditions described [here](file.md) apply, too.

## Query Parameters

Validation around duplicate query parameters is not in the scope of test-engine.
See https://github.com/admin-shell-io/aas-specs-api/issues/313 for details.

## Operations

Methods like `InvokeOperation` are not executed as we cannot check their side-effects in a generic way

## Non-Applicability of Serialization Modifiers

In Part 2, Section 11.3 "Applicability of SerializationModifiers" it is not specified what Applicability means in the context of HTTP/REST. 
For current scope/release, the test-engine expects below behavior: 
 
**For level and extent:** 
A server should not throw any error for not applicable query parameters, i.e., Level and Extent. The server should in this case, ignore the query parameters and return the serialization of the element. 

**For content:**
The server should result in an error, usually 404.

See https://github.com/admin-shell-io/aas-specs-api/issues/327 for details.

## GetAllSubmodelElements

`/submodel-elements` is under-specified for the different SerializationModifiers. 
See the following issues for details:
* https://github.com/admin-shell-io/aas-specs-api/issues/265 
* https://github.com/admin-shell-io/aas-specs-api/issues/185 
* https://github.com/admin-shell-io/aas-specs-api/issues/246 

## Pagination

It is possible that the server is modified during the pagination request. However, the specifications are underdefines for such scenario. 
Thus, for the current scope of the test-engine, modification around pagination is not being considered.

Cursor has to be serialized as string, even though it is an integer. No other data type is allowed. 
As the  specification allows the cursor in the response to be both Base64UrlEncoded as well as not-encoded, the test-engine supports both. 

