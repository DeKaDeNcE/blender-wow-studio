//
// Created by cromon on 06.05.2018.
//

#ifndef CYTHON_BLP_BLPCONVERTEXCEPTION_H
#define CYTHON_BLP_BLPCONVERTEXCEPTION_H

#include <exception>
#include <string>
#include <utility>

namespace python_blp {
    class BlpConvertException : public std::exception {
        std::string mMessage;

    public:
        BlpConvertException(std::string message) : mMessage(std::move(message)) {

        }

        const char *what() const noexcept override {
            return mMessage.c_str();
        }
    };
}


#endif //CYTHON_BLP_BLPCONVERTEXCEPTION_H
