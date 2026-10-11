#include <msp430f5529.h>
#define CPU_F ((double)1000000)
#define delay_us(x)__delay_cycles((long)(CPU_F*(double)x/1000000.0))
#define delay_ms(x)__delay_cycles((long)(CPU_F*(double)x/1000.0))
unsigned int DC_motor=100;
unsigned int i=100;
unsigned int a=0;
unsigned int distime=0;
unsigned char data[] = {0xC0,0xF9,0xA4,0xB0,0x99,0x92,0x82,0xF8,0x80,0x90};
unsigned int j=0;
unsigned int Cycle[2];
unsigned int p=0;
unsigned int disnum;
unsigned int sum=0,n=0,ave=0;
unsigned int tjl[500],tjli=0;
void Duoji_init()
{
    P2DIR |= BIT0;                            // P2.0 output
    P2SEL |= BIT0;                            // P2.0 options select
    TA1CCR0 = 20000;                          // PWM Period = 20ms
    TA1CCTL1 = OUTMOD_7;                      // CCR1 reset/set
    TA1CCR1 = 1500;                           // CCR1 PWM duty cycle
    TA1CTL = TASSEL_2 + MC_1 + TACLR ;        // SMCLK, up mode, clear TAR.
}

void DC_Motor_init()
{
    P2DIR |= BIT4 + BIT5;                      // P2.4,P2.5 output.
    P2SEL |= BIT4 + BIT5;                      // P2.4,P2.5 options select
    TA2CCR0 = 158;                             // PWM Period = 0.2ms
    TA2CCTL1 = OUTMOD_7;                       // CCR1 reset/set
    TA2CCR1 = 100;                               // CCR1 PWM duty cycle
    TA2CCTL2 = OUTMOD_7;                       // CCR2 reset/set
    TA2CCR2 = 100;                               // CCR2 PWM duty cycle
    TA2CTL = TASSEL_2 + MC_1 + TACLR ;         // SMCLK, up mode, clear TAR.
}

void display_init()
{
P3DIR = 0xff;                 //设置P1，P2的IO方向为输出
P3OUT = 0xff;
P4DIR = 0xff;
P4OUT = 0xff;
}

void delay(void)//延时
{
    unsigned int k;
    for(k = 100;k > 0;k--)
         _NOP();
}

void display(int mid)
{
            P3OUT = data[mid/1000];        //输出段选信号
            P4OUT = ~(1<<j);        //4.0(d1)
            delay();
            j++;
            P3OUT = data[mid%1000/100];        //输出段选信号
            P4OUT = ~(1<<j);        //4.1(d2)
            delay();
            j++;
            P3OUT = data[mid%1000%100/10];        //输出段选信号
            P4OUT = ~(1<<j);        //4.2(d3)
            delay();
            j++;
            P3OUT = data[mid%1000%100%10];        //输出段选信号
            P4OUT = ~(1<<j);       //4.3(d4)
            delay();
            j=0;
           }

void caiyang()
{
    P1DIR &= ~BIT2;
    P1SEL |= BIT2;
    TA0CCTL1 = CM0 + SCS + CAP + CCIE;
}


void main(void)
{
    WDTCTL = WDTPW + WDTHOLD;                  // Stop WDT
    P1DIR |= BIT0;
    P1OUT &= ~BIT0;
    Duoji_init();                              //
    DC_Motor_init();
    display_init();
    TA0CCTL0 = CCIE;                           // CCR0 interrupt enabled
    TA0CCR0 = 5000;                    // ?
    TA0CTL = TASSEL_2 + MC_1 + TACLR;    // SMCLK, upmode, clear TAR
    TA2CCR1 = DC_motor;
    TA2CCR2 = DC_motor;
    __bis_SR_register(GIE);          // Enter LPM0, enable interrupts
    caiyang();
    while(1)
    {
        display(distime);
    }
}

#pragma vector=TIMER0_A0_VECTOR                // Timer0 A0 interrupt service routine
__interrupt void TIMER0_A0_ISR(void)
{
    if(a==1000)a=0,n=0;
    a+=5;
        switch(P6IN&0x1f)
      {
        case 0x0f:                            //you da
           TA1CCR1 = 1500+4.5*i;
           break;
        case 0x17:                           //you xiao
           TA1CCR1 = 1500+2*i;
           break;
        case 0x1b:                               //zhi
           TA1CCR1 = 1500;
           break;
        case 0x1d:                             //zuo xiao
           TA1CCR1 = 1500-2*i;
           break;
        case 0x1e:
           TA1CCR1 = 1500-4*i;                 //zuo da
           break;
        case 0x00:
           TA1CCR1 = 1500;
           break;
        default:
           break;
      }
}

#pragma vector=TIMER0_A1_VECTOR
__interrupt void TIMER_A0(void)
{
    if(a>=0)
    {
        n+=1;
    }
    if(a==1000)
    {
        distime=n;
    }
    TA0CCTL1 &= ~CCIFG;
}
