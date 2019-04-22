#include<bits/stdc++.h>
using namespace std;
#define MAXV 2147483647
#define MINV -2147483647
#define SYC ios_base::sync_with_stdio(0); cin.tie(0)
#define FR freopen("/Users/naveen/Documents/online_code/input.txt","r",stdin)
#define FW freopen("/Users/naveen/Documents/online_code/output.txt","w",stdout)
#define M 1000000007
struct Source{
    int source_id;
    float packet_sending_rate;
    float source_bandwidth;
    float source_to_switch_time;
    bool free_source;
    float busy_link;
};

struct Packet{
    float time_of_birth;
    float time_of_dead;
    int source_id;
    int packet_id;
};

struct Event{
    int type;
    int source_id;
    int packet_id;
    float time_stamp;
};
class cmp
{
public:
    bool operator() (Event a, Event b)
    {
        if(a.time_stamp<b.time_stamp)return false;

        else if(a.time_stamp==b.time_stamp){

            return !(a.type>b.type);

        }
        return true;

    }
};

bool compare(Packet a,Packet b){
    if(a.time_of_birth<b.time_of_birth){
        return true;
    }
    return false;
}
float    random_between_two_int(float min, float max)
{
    return (min + 1) + (((float) rand()) / (float) RAND_MAX) * (max - (min + 1));
}

int main(){
//    FR;
//    FW;
    int number_of_source=1; // number of source
    int length_of_packet; // length of packet in networking
    float source_bandwidth;
    //    cout<<"Enter number of source in Network :";
    cin>>number_of_source;
    //    cout<<"Length of packet :";
    cin>>length_of_packet;
    //    cout<<"bandwidth of source:";
    cin>>source_bandwidth;
    Source source_obj[number_of_source];
    float max_sending_rate,sending_inc=0.1;

    vector<pair<float, float>> result;
    //    cout<<"Maximum sending rate :";
    cin>>max_sending_rate;
    float sink_bandwidth,switch_to_sink_time;
    //    cout<<"Enter sink bandwidth :";
    cin>>sink_bandwidth;
    //    cout<<endl;
    switch_to_sink_time=length_of_packet/sink_bandwidth;
    float tmp;

    //        cout<<"Time to generate packet in each source :";
    cin>>tmp;
    //    cout<<endl;

    while(sending_inc<max_sending_rate){

        //    cout<<"Enter all source packet sending rate and source bandwidth: "<<endl<<endl;
        for(int i = 0 ; i<number_of_source ; i++){
            //        cout<<"Enter source "<<i+1<<" packet sending rate :";
            source_obj[i].source_id=i;
            //        cin>>source_obj[i].packet_sending_rate;
            source_obj[i].packet_sending_rate=sending_inc;
            //        cout<<endl;
            //        cout<<"Enter source "<<i+1<<" source bandwidth :";
            //        cin>>source_obj[i].source_bandwidth;
            source_obj[i].source_bandwidth=source_bandwidth;

            source_obj[i].source_to_switch_time=length_of_packet/source_obj[i].source_bandwidth;
            //        cout<<endl;
            source_obj[i].free_source=true;
            source_obj[i].busy_link=0.0;
            //        cout<<source_obj[i].packet_sending_rate<<endl;
        }
        priority_queue<Event,vector<Event>,cmp>q;
        int cnt=0;
        vector<Packet>packet;

        for(int i =0 ; i< number_of_source ; i++){
            float randNum =random_between_two_int(0,2);
            for(float j =randNum ; j<= tmp ; j+=source_obj[i].packet_sending_rate){
                q.push({0,source_obj[i].source_id,cnt,j,});
                packet.push_back({j,MAXV,source_obj[i].source_id,cnt});
                cnt++;
            }
        }

        //    priority_queue<Event,vector<Event>,cmp>p=q;
        //    while(!p.empty()){
        //        Event s =p.top();
        //        cout<<s.type<<" "<<s.source_id<<" "<<s.packet_id<<" "<<s.time_stamp<<endl;
        //        p.pop();
        //    }
        bool switch2_free=true,sink_free=true;

        float sink_busy_time=0.0;

        while(!q.empty()){
            Event p =q.top();
            q.pop();
            int type=p.type,source=p.source_id,packet_id=p.packet_id;

            float time_stamp=p.time_stamp;

            bool free_source=source_obj[source].free_source;

            if(type==0){
                if(free_source==true){

                    type=1;
                    source_obj[source].free_source=false;
                    time_stamp=time_stamp+source_obj[source].source_to_switch_time;
                    q.push({type,source,packet_id,time_stamp});
                    source_obj[source].busy_link=time_stamp;

                }
                else{

                    time_stamp=source_obj[source].busy_link;
                    q.push({type,source,packet_id,time_stamp});
                }
            }
            else if(type==1){
                if(switch2_free){
                    switch2_free=false;
                    source_obj[source].free_source=true;
                    type=2;
                    q.push({type,source,packet_id,time_stamp});
                }
                else{
                    time_stamp=sink_busy_time;
                    source_obj[source].busy_link=time_stamp;
                    q.push({type,source,packet_id,time_stamp});
                }
            }
            else if(type==2){
                if(sink_free){
                    sink_free=false;
                    switch2_free=true;
                    time_stamp=time_stamp+switch_to_sink_time;
                    type=3;
                    sink_busy_time=time_stamp;
                    q.push({type,source,packet_id,time_stamp});
                }
                else{
                    time_stamp=sink_busy_time;
                    q.push({type,source,packet_id,time_stamp});
                }
            }
            else{
                //            q.pop();
                sink_free=true;
                packet[packet_id].time_of_dead=time_stamp;
            }

        }

        //        sort(packet.begin(),packet.end(),compare);

        //        cout<<"final"<<endl;
        float rend=0.0;
        for(int i =0 ; i< cnt ; i++){
            //            cout<<packet[i].packet_id<<" "<<packet[i].source_id <<" "<<packet[i].time_of_birth <<" "<<packet[i].time_of_dead<<endl;
            rend+=(packet[i].time_of_dead-packet[i].time_of_birth);
        }
        result.push_back({sending_inc,rend/cnt});
        sending_inc+=0.1;

    }
    for(auto x:result){
        cout<<x.first<<" "<<x.second<<endl;
    }
    return 0;
}
