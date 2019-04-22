// #include "/Users/naveen/stdc++.h"
#include<stdio.h>
#include<iostream>
#include<bits/stdc++.h>
using namespace std;
#define MAXV 2147483647
#define MINV -2147483647
typedef long long int ll;
#define MAX 1000003

#define SYC ios_base::sync_with_stdio(0); cin.tie(0)
#define FR freopen("/Users/naveen/Documents/online_code/input.txt","r",stdin)
#define FW freopen("/Users/naveen/Documents/online_code/output.txt","w",stdout)
#define REP(i, a, b) for (int i = int(a); i <= int(b); i++)

struct packet
{
    double start_time;
    double end_time;
    double crnt_time;
    int packet_id;
    int packet_source;
    int type;
};

 struct source
{
    int source_id;
    double source_to_switch_time;
    double sending_rate;
};
struct swich
{
    double last_arrived;
    int arrived_from_source;
};

struct comp{
    bool operator()(packet*  p1, packet* p2)
    {
        return p1->crnt_time >= p2->crnt_time;
    }
};
double getgenerator(double sending_rate){
    default_random_engine generator;
    uniform_real_distribution<double> distribution(0.0,1.0);
    double number=0.0;
//    for(int i =0 ; i< 10; i++){
             number = distribution(generator);
//    cout<<number;
//    }
    double t=-1.0*log(1-number)/sending_rate;
    return t;
}


int main(){
    double last_arrived_at_sink=0;
    double swich_to_sink_time;
    double busy_time[50];
    // FR;
    // FW;
    
//    for(int i =0 ; i< 10; i++)
//        cout<<" "<<getgenerator(i+0.2)<<endl;
//    cout<<"Enter the number of nodes you want to use\n";
    
    int number_of_s;cin>>number_of_s;
    source src[number_of_s];
    
//    cout<<"Enter the sending rate and time to reach switch for each source\n";
    for(int i=0;i<number_of_s;i++){
        src[i].source_id=i;
        cin>>src[i].sending_rate>>src[i].source_to_switch_time;
    }
//    cout<<"Enter the time to reach sink from switch\n";
    cin>>swich_to_sink_time;
    
    double snt;
    cin>>snt;
    double cnt=0;
    
    int max_queue_size;
    cin>>max_queue_size;
    
    default_random_engine generator;
    uniform_real_distribution<double> distribution(0.0,1.0);
    
    while(cnt<snt){
        last_arrived_at_sink=0;
        cnt+=.1;
    priority_queue<packet*,vector<packet*>,comp> Q;
    packet pck[200000];
    for(int i=0;i<50;i++)busy_time[i]=0;
    int maxx_allowed=200;
    int no_of_packets=0;
        
    for(int i=0;i<number_of_s;i++){
        double number=distribution(generator);
//        src[i].sending_rate
        double t=-1.0*log(1-number)/(cnt);
 
//        cout<<"t"<<t<<endl;
        double temp=0.0;
        for(double tot_pck=0 ; tot_pck<maxx_allowed ; tot_pck++ )
        {
            
            temp=temp+t;
//            cout<<t<<" "<<temp<<" ";
            pck[no_of_packets].start_time=temp;
            pck[no_of_packets].end_time=9999;
            pck[no_of_packets].crnt_time=temp;
            pck[no_of_packets].packet_id=no_of_packets;
            pck[no_of_packets].packet_source=i;
            pck[no_of_packets].type=0;
            Q.push(pck+no_of_packets);
            no_of_packets++;
        }
        
    }
    int count_queue=0;
    int count_drop[number_of_s];
        for(int i = 0 ; i< number_of_s ; i++){
            count_drop[i]=0.0;
        }
    while(!Q.empty()){
        packet* p=Q.top();
        Q.pop();
        //cout<<"packet_id="<<p->packet_id<<" crnt_time "<<p->crnt_time<<"type="<<p->type<<"\n";
        if(p->type==0){
            int from_source=p->packet_source;
            if(p->start_time >= busy_time[from_source]){
                p->crnt_time=p->start_time+src[from_source].source_to_switch_time;
                p->type=1;
                busy_time[from_source]=p->crnt_time;
                
                if(count_queue>=max_queue_size){
                    pck[p->packet_id].type=-1;
                    count_drop[p->packet_source]++;
                    
                }else{
                    Q.push(p);
                    count_queue++;
                }
            }
            else if(p->start_time + src[from_source].source_to_switch_time >= busy_time[from_source]){
                p->crnt_time=busy_time[from_source]+src[from_source].source_to_switch_time;
                p->type=1;
                busy_time[from_source]=p->crnt_time;
                
                if(count_queue>=max_queue_size){
                    
                    pck[p->packet_id].type=-1;
                    count_drop[p->packet_source]++;
                    
                }
                else{
                    Q.push(p);
                    count_queue++;
                }
            }
        }
        else if(p->type ==1){
            if(p->crnt_time >= last_arrived_at_sink){
                p->end_time=p->crnt_time + swich_to_sink_time;
                last_arrived_at_sink = p->end_time;
                p->type=2;
                count_queue--;
            }
            else if(p->crnt_time + swich_to_sink_time >= last_arrived_at_sink){
                p->end_time=last_arrived_at_sink+swich_to_sink_time;
                last_arrived_at_sink=p->end_time;
                p->type=2;
                count_queue--;
            }
        }
//        cout<<count_queue<<" ";
    }
    double dlay=0;
        double delay[number_of_s];
        int count[number_of_s];
        
        for(int i =0 ; i< number_of_s ; i++){
            delay[i]=0.0;
            count[i]=0;
        }
    int total_packets=0;
    for(int i=0;i<no_of_packets;i++){
        //if(pck[i].end_time < 10){
        
        count[pck[i].packet_source]++;
        delay[pck[i].packet_source]+=(pck[i].end_time-pck[i].start_time);
        dlay+=(pck[i].end_time-pck[i].start_time) ;
        total_packets++;
        //}
    }
        for(int i =0 ;  i< number_of_s ; i++){
//            cout<<delay[i]/count[i]<<" ";
            cout<<count_drop[i]<<" ";
        }
//        for(int i =0 ;  i< number_of_s ; i++){
//                        cout<<delay[i]/count[i]<<" ";
////            cout<<count_drop[i]<<" ";
//        }
        cout<<cnt;
//        cout<<total_packets<<" "<<count[0]<<" "<<count[1]<<" "<<count[2]<<" "<<(dlay/total_packets);
        cout<<endl;
    }
    return 0;
}

















