/* --COPYRIGHT--,BSD
 * Copyright (c) 2017, Texas Instruments Incorporated
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * *  Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *
 * *  Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * *  Neither the name of Texas Instruments Incorporated nor the names of
 *    its contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
 * OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
 * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 * --/COPYRIGHT--*/
//***************************************************************************************
//  Blink the LED Demo - Software Toggle P1.0
//
//  Description; Toggle P1.0 inside of a software loop using DriverLib.
//  ACLK = n/a, MCLK = SMCLK = default DCO
//
//                MSP4302433
//             -----------------
//         /|\|              XIN|-
//          | |                 |
//          --|RST          XOUT|-
//            |                 |
//            |             P1.0|-->LED
//
//  E. Chen
//  Texas Instruments, Inc
//  October 2017
//  Built with Code Composer Studio v7
//***************************************************************************************

#include "gpio.h"
#include <driverlib.h>
// #include <bool.h>

// this should be done with paired arrays of input to output arrays
// config


#define button_delay 1000

void ResetLocalIndicators ()
{
    GPIO_setOutputLowOnPin(
        GPIO_PORT_P2,
        GPIO_PIN3
    );
    GPIO_setOutputLowOnPin(
        GPIO_PORT_P2,
        GPIO_PIN5
    );
    GPIO_setOutputLowOnPin(
        GPIO_PORT_P2,
        GPIO_PIN7
    );
    GPIO_setOutputLowOnPin(
        GPIO_PORT_P3,
        GPIO_PIN2
    );
    // interupt line
    GPIO_setOutputHighOnPin(
        GPIO_PORT_P1,
        GPIO_PIN0
    );

}
int main(void) {

    volatile uint32_t i;
    volatile bool InterupFlag = false, LastInterupFlag = false;

    // Stop watchdog timer
    WDT_A_hold(WDT_A_BASE);


    // Set up Interupt Flag output direction
    GPIO_setAsOutputPin(
        GPIO_PORT_P1,
        GPIO_PIN0
        );
    // clear Interupt Flag 
    GPIO_setOutputHighOnPin (GPIO_PORT_P1, GPIO_PIN0);
    // Set Reset Flag Input direction
    GPIO_setAsInputPinWithPullUpResistor(
        GPIO_PORT_P1,
        GPIO_PIN1
        );

    // Set up feedback output direction
    GPIO_setAsOutputPin(
        GPIO_PORT_P2,
        GPIO_PIN3
        );

    // Set up feedback output direction
    GPIO_setAsOutputPin(
        GPIO_PORT_P2,
        GPIO_PIN5
        );
    // Set up feedback output direction
    GPIO_setAsOutputPin(
        GPIO_PORT_P2,
        GPIO_PIN7
        );
    // Set up feedback output direction
    GPIO_setAsOutputPin(
        GPIO_PORT_P3,
        GPIO_PIN2
        );
    // Set up buttons direction
    GPIO_setAsInputPin(
        GPIO_PORT_P2,
        GPIO_PIN2
        );
    // Set up buttons direction
    GPIO_setAsInputPin(
        GPIO_PORT_P2,
        GPIO_PIN4
        );
    // Set up buttons direction
    GPIO_setAsInputPin(
        GPIO_PORT_P2,
        GPIO_PIN6
        );
    // Set up buttons direction
    GPIO_setAsInputPin(
        GPIO_PORT_P3,
        GPIO_PIN1
        );
    // Disable the GPIO power-on default high-impedance mode
    // to activate previously configured port settings
    PMM_unlockLPM5();

    GPIO_setOutputLowOnPin (
        GPIO_PORT_P2,
        GPIO_PIN3
        );
    GPIO_setOutputLowOnPin (
        GPIO_PORT_P2,
        GPIO_PIN5
        );
    GPIO_setOutputLowOnPin (
        GPIO_PORT_P2,
        GPIO_PIN7
        );
    GPIO_setOutputLowOnPin (
        GPIO_PORT_P3,
        GPIO_PIN2
        );
    int countdown=0;

    while(1)
    {
// this should be done with paired arrays of input to output arrays
        if (!GPIO_getInputPinValue(
                GPIO_PORT_P2,
                GPIO_PIN2
                ))
            {
                InterupFlag = true;
                GPIO_toggleOutputOnPin(
                    GPIO_PORT_P2,
                    GPIO_PIN3
                    );
                countdown = button_delay;
                while (countdown > 0)  
                {
                    if (!GPIO_getInputPinValue(
                            GPIO_PORT_P2,
                            GPIO_PIN2
                            ))
                            {
                                countdown = button_delay;
                            }
                    else 
                            {
                                countdown--;
                            }

                }
            }
        if (!GPIO_getInputPinValue(
                GPIO_PORT_P2,
                GPIO_PIN4
                ))
            {
                InterupFlag = true;
                GPIO_toggleOutputOnPin(
                    GPIO_PORT_P2,
                    GPIO_PIN5
                    );
                countdown = button_delay;
                while (countdown > 0)  
                {
                    if (!GPIO_getInputPinValue(
                            GPIO_PORT_P2,
                            GPIO_PIN4
                            ))
                            {
                                countdown = button_delay;
                            }
                    else 
                            {
                                countdown--;
                            }

                }            }
        if (!GPIO_getInputPinValue(
                GPIO_PORT_P2,
                GPIO_PIN6
                ))
            {
                InterupFlag = true;
                GPIO_toggleOutputOnPin(
                    GPIO_PORT_P2,
                    GPIO_PIN7
                    );
                countdown = button_delay;
                while (countdown > 0)  
                {
                    if (!GPIO_getInputPinValue(
                            GPIO_PORT_P2,
                            GPIO_PIN6
                            ))
                            {
                                countdown = button_delay;
                            }
                    else 
                            {
                                countdown--;
                            }

                }            }
        if (!GPIO_getInputPinValue(
                GPIO_PORT_P3,
                GPIO_PIN1
                ))
            {
                InterupFlag = true;
                GPIO_toggleOutputOnPin(
                    GPIO_PORT_P3,
                    GPIO_PIN2
                    );
                countdown = button_delay;
                while (countdown > 0)  
                {
                    if (!GPIO_getInputPinValue(
                            GPIO_PORT_P3,
                            GPIO_PIN1
                            ))
                            {
                                countdown = button_delay;
                            }
                    else 
                            {
                                countdown--;
                            }

                }            }
        // reset line
        if (!GPIO_getInputPinValue(
                GPIO_PORT_P1,
                GPIO_PIN1
                ))
            {
                InterupFlag = false;
                countdown = button_delay;
                while (countdown > 0)  
                {
                    if (!GPIO_getInputPinValue(
                            GPIO_PORT_P3,
                            GPIO_PIN1
                            ))
                            {
                                countdown = button_delay;
                            }
                    else 
                            {
                                countdown--;
                            }

                }            }
        // did anything happen?
        if (InterupFlag != LastInterupFlag)
        {
            if (InterupFlag)
            {
                    GPIO_setOutputLowOnPin(
                        GPIO_PORT_P1,
                        GPIO_PIN0
                    );

            }
            else  
            {
                ResetLocalIndicators();
            }
        }
        LastInterupFlag = InterupFlag;
    }
}
