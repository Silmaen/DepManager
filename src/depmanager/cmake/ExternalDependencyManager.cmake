#[===================================================[.rst:
ExternalDependencyManager
-------------------------

Set of tools to manage external libraries for C++
projects.
#]===================================================]
get_filename_component(EDM_ROOT_PATH ${CMAKE_CURRENT_LIST_DIR} DIRECTORY)
find_program(EDM_INTERNAL_COMMAND depmanager)

function(edm_to_std_arch INPUT OUTPUT)
    string(REPLACE "AMD" "x86_" TMP ${INPUT})
    set(${OUTPUT} ${TMP} PARENT_SCOPE)
endfunction()
function(edm_to_std_compiler INPUT OUTPUT)
    if (${INPUT} MATCHES "MSVC" OR ${INPUT} MATCHES "Clang-cl")
        set(${OUTPUT} "msvc" PARENT_SCOPE)
    elseif (${INPUT} MATCHES "GNU" OR ${INPUT} MATCHES "Clang")
        set(${OUTPUT} "gnu" PARENT_SCOPE)
    else ()
        set(${OUTPUT} "unknown" PARENT_SCOPE)
    endif ()
endfunction()

function(edm_get_data_path OUTPUT)
    execute_process(COMMAND ${EDM_INTERNAL_COMMAND} info basedir
            OUTPUT_VARIABLE RESULT)
    string(STRIP "${RESULT}" RESULT)
    set(${OUTPUT} ${RESULT} PARENT_SCOPE)
endfunction()

function(edm_find_package PACKAGE)
    cmake_parse_arguments(FP "QUIET;TRACE" "VERSION;TYPE;ARCH;OS;COMPILER" "" ${ARGN})
    if (FP_VERSION)
        set(PREDICATE "${PACKAGE}/${FP_VERSION}")
    else ()
        set(PREDICATE "${PACKAGE}/*")
    endif ()
    set(SEARCH_OPTIONS "")
    if (FP_TYPE)
        string(TOLOWER "${FP_TYPE}" FP_TYPE)
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -t ${FP_TYPE}")
    endif ()
    if (FP_ARCH)
        edm_to_std_arch(${FP_ARCH} TRUE_ARCH)
    else ()
        edm_to_std_arch(${CMAKE_SYSTEM_PROCESSOR} TRUE_ARCH)
    endif ()
    set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -a ${TRUE_ARCH}")
    if (FP_OS)
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -o ${FP_OS}")
    else ()
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -o ${CMAKE_SYSTEM_NAME}")
    endif ()
    if (FP_COMPILER)
        edm_to_std_compiler(${FP_COMPILER} TRUE_COMPILER)
    else ()
        edm_to_std_compiler(${CMAKE_CXX_COMPILER_ID} TRUE_COMPILER)
    endif ()
    set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -c ${TRUE_COMPILER}")

    set(CMD "${EDM_INTERNAL_COMMAND} search -r -b -p ${PREDICATE} ${SEARCH_OPTIONS}")
    if (FP_TRACE)
        message(STATUS "QUERY: ${CMD}")
    endif()
    string(REPLACE " " ";" CMD ${CMD})
    execute_process(COMMAND ${CMD}
            OUTPUT_VARIABLE TMP)
    string(STRIP "${TMP}" TMP)
    string(REPLACE "\\" "/" TMP "${TMP}")
    if ("${TMP}" STREQUAL "")
        if (NOT FP_QUIET)
            message(FATAL_ERROR "Could not found suitable versions of ${PACKAGE}")
        endif ()
    endif ()
    if (FP_TRACE)
        message(STATUS "RESULT: ${TMP}")
    endif()
    list(PREPEND CMAKE_PREFIX_PATH ${TMP})
    find_package(${PACKAGE} REQUIRED)

endfunction()



