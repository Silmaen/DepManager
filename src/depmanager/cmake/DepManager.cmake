#[===================================================[.rst:
ExternalDependencyManager
-------------------------

Set of tools to manage external libraries for C++
projects.
#]===================================================]
get_filename_component(DM_ROOT_PATH ${CMAKE_CURRENT_LIST_DIR} DIRECTORY)
find_program(DM_INTERNAL_COMMAND depmanager)
set(DM_ACTIVE ON CACHE BOOL "Depmanager is active")

function(dm_to_std_arch INPUT OUTPUT)
    string(REPLACE "AMD" "x86_" TMP ${INPUT})
    set(${OUTPUT} ${TMP} PARENT_SCOPE)
endfunction()

function(dm_to_std_compiler INPUT OUTPUT)
    if (${INPUT} MATCHES "MSVC" OR ${INPUT} MATCHES "Clang-cl")
        set(${OUTPUT} "msvc" PARENT_SCOPE)
    elseif (${INPUT} MATCHES "GNU" OR ${INPUT} MATCHES "Clang")
        set(${OUTPUT} "gnu" PARENT_SCOPE)
    else ()
        set(${OUTPUT} "unknown" PARENT_SCOPE)
    endif ()
endfunction()

function(dm_get_data_path OUTPUT)
    execute_process(COMMAND ${DM_INTERNAL_COMMAND} info basedir
            OUTPUT_VARIABLE RESULT)
    string(STRIP "${RESULT}" RESULT)
    set(${OUTPUT} ${RESULT} PARENT_SCOPE)
endfunction()

function(dm_get_glibc OUTPUT)
    # Créer un fichier source C pour tester la version de glibc
    if (${CMAKE_SYSTEM_NAME} STREQUAL "Linux")

        execute_process(COMMAND ldd --version OUTPUT_VARIABLE glibc_version RESULT_VARIABLE RES)
        if (${RES} EQUAL 0)
            string(REGEX MATCH "[0-9]+\\.[0-9]+" glibc_version "${glibc_version}")
            set(${OUTPUT} ${CMAKE_MATCH_0} PARENT_SCOPE)
            message(STATUS "Found Glib_C: ${CMAKE_MATCH_0}")
        else ()
            set(${OUTPUT} "" PARENT_SCOPE)
            message("Unable to determine GLIBC version.")
        endif ()
    else()
        set(${OUTPUT} "" PARENT_SCOPE)
    endif()
endfunction()

function(dm_load_package PACKAGE)
    cmake_parse_arguments(FP "REQUIRED;TRACE" "VERSION;KIND;ARCH;OS;COMPILER;GLIBC" "" ${ARGN})
    if (FP_VERSION)
        set(PREDICATE "${PACKAGE}/${FP_VERSION}")
    else ()
        set(PREDICATE "${PACKAGE}/*")
    endif ()
    set(SEARCH_OPTIONS "")
    if (FP_KIND)
        string(TOLOWER "${FP_KIND}" FP_TYPE)
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -k ${FP_KIND}")
    endif ()
    if (FP_ARCH)
        dm_to_std_arch(${FP_ARCH} TRUE_ARCH)
    else ()
        dm_to_std_arch(${CMAKE_SYSTEM_PROCESSOR} TRUE_ARCH)
    endif ()
    set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -a ${TRUE_ARCH}")
    if (FP_OS)
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -o ${FP_OS}")
    else ()
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -o ${CMAKE_SYSTEM_NAME}")
    endif ()
    if (FP_COMPILER)
        dm_to_std_compiler(${FP_COMPILER} TRUE_COMPILER)
    else ()
        dm_to_std_compiler(${CMAKE_CXX_COMPILER_ID} TRUE_COMPILER)
    endif ()
    set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -c ${TRUE_COMPILER}")

    if (FP_GLIBC)
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -g ${FP_GLIBC}")
    else ()
        dm_get_glibc(O_GLIBC)
        if (O_GLIBC)
            set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -g ${O_GLIBC}")
        endif ()
    endif ()

    set(CMD "${DM_INTERNAL_COMMAND} get -p ${PREDICATE} ${SEARCH_OPTIONS}")
    if (FP_TRACE)
        message(STATUS "QUERY: ${CMD}")
    endif()
    string(REPLACE " " ";" CMD ${CMD})
    execute_process(COMMAND ${CMD}
            OUTPUT_VARIABLE OUT
            RESULT_VARIABLE RES
            ERROR_VARIABLE ERR)
    if (${RES} EQUAL 0)
        string(STRIP "${OUT}" OUT)
        string(REPLACE "\\" "/" OUT "${OUT}")
        if ("${OUT}" STREQUAL "")
            if (FP_REQUIRED)
                message(FATAL_ERROR "Could not found suitable versions of ${PACKAGE}")
            endif ()
        endif ()
        if (FP_TRACE)
            message(STATUS "RESULT: ${OUT}")
        endif()
        list(PREPEND CMAKE_PREFIX_PATH ${OUT})
        set(CMAKE_PREFIX_PATH ${CMAKE_PREFIX_PATH} PARENT_SCOPE)
    else ()
        message(WARNING "${CMD}")
        message(FATAL_ERROR "Depmanager error (${RES}) while searching for ${PACKAGE}: ${OUT} ${ERR}, ${CMD}")
    endif ()
endfunction()

function(dm_find_package PACKAGE)
    cmake_parse_arguments(FP "QUIET;REQUIRED" "" "" ${ARGN})
    dm_load_package(${ARGN} ${PACKAGE})
    if (FP_QUIET)
        set(FIND_OPTIONS ${FIND_OPTION} QUIET)
    endif()
    if (FP_REQUIRED)
        set(FIND_OPTIONS ${FIND_OPTION} REQUIRED)
    endif()
    find_package(${PACKAGE} ${FIND_OPTIONS} CONFIG)
endfunction()

function(dm_load_environment)
    cmake_parse_arguments(FP "QUIET" "PATH;KIND;ARCH;OS;COMPILER;GLIBC" "" ${ARGN})
    # decoding parameters
    set(SEARCH_OPTIONS "")
    if (FP_PATH)
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} --config ${FP_PATH}")
    else ()
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} --config ${CMAKE_SOURCE_DIR}")
    endif ()
    if (FP_KIND)
        string(TOLOWER "${FP_KIND}" FP_TYPE)
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -k ${FP_KIND}")
    endif ()
    if (FP_ARCH)
        dm_to_std_arch(${FP_ARCH} TRUE_ARCH)
    else ()
        dm_to_std_arch(${CMAKE_SYSTEM_PROCESSOR} TRUE_ARCH)
    endif ()
    set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -a ${TRUE_ARCH}")
    if (FP_OS)
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -o ${FP_OS}")
    else ()
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -o ${CMAKE_SYSTEM_NAME}")
    endif ()
    if (FP_COMPILER)
        dm_to_std_compiler(${FP_COMPILER} TRUE_COMPILER)
    else ()
        dm_to_std_compiler(${CMAKE_CXX_COMPILER_ID} TRUE_COMPILER)
    endif ()
    set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -c ${TRUE_COMPILER}")
    if (FP_GLIBC)
        set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -g ${FP_GLIBC}")
    else ()
        dm_get_glibc(O_GLIBC)
        if (O_GLIGC)
            set(SEARCH_OPTIONS "${SEARCH_OPTIONS} -g ${O_GLIGC}")
        endif ()
    endif ()
    set(CMD "${DM_INTERNAL_COMMAND} load ${SEARCH_OPTIONS}")
    STRING(REPLACE " " ";" CMD ${CMD})
    execute_process(COMMAND ${CMD}
            RESULT_VARIABLE RES
            OUTPUT_VARIABLE OUT
            ERROR_VARIABLE ERR
    )
    if (${RES} EQUAL 0)
        string(STRIP "${OUT}" OUT)
        string(REPLACE "\\" "/" OUT "${OUT}")
        if ("${OUT}" STREQUAL "")
            if (NOT FP_QUIET)
                message(FATAL_ERROR "Depmanager loading environment empty.")
            else ()
                message(WARNING "Depmanager loading environment empty.")
            endif ()
        else ()
            list(PREPEND CMAKE_PREFIX_PATH ${OUT})
            set(CMAKE_PREFIX_PATH ${CMAKE_PREFIX_PATH} PARENT_SCOPE)
        endif ()
    else ()
        message(FATAL_ERROR "Depmanager error (${RES}) while loading environment: ${OUT} ${ERR}")
    endif ()
endfunction()
