#include <bits/stdc++.h>
using namespace std;

struct Point { double lat{}, lng{}; };
struct Pickup { string name; Point p; int demand{}; int remaining{}; };

static inline double toRad(double d){ return d * M_PI / 180.0; }

// Haversine distance in meters
static double haversineMeters(const Point&a, const Point&b){
    static const double R = 6371000.0; // Earth radius meters
    double phi1 = toRad(a.lat), phi2 = toRad(b.lat);
    double dphi = toRad(b.lat - a.lat), dlmb = toRad(b.lng - a.lng);
    double h = sin(dphi/2)*sin(dphi/2) + cos(phi1)*cos(phi2)*sin(dlmb/2)*sin(dlmb/2);
    return 2.0 * R * atan2(sqrt(h), sqrt(1.0 - h));
}

// Approximate travel time in seconds from meters assuming ~40km/h
static double metersToSeconds(double meters){ return meters / 11.11; }

struct TripLegInfo {
    string name;
    double meters{};
    double seconds{};
};

struct TripInfo {
    vector<TripLegInfo> legs; // depot->stop1, stop1->stop2, ..., stopN->depot (last reported separately)
    double totalMeters{};
    double totalSeconds{};
    double backMeters{};
    double backSeconds{};
};

static string fmtMiles(double meters){
    double miles = meters / 1609.34; 
    ostringstream oss; oss.setf(std::ios::fixed); oss<<setprecision(1)<<miles<<" mi"; return oss.str();
}
static string fmtMinutes(double seconds){
    int mins = (int)round(seconds/60.0); ostringstream oss; oss<<mins<<" min"; return oss.str();
}

static string jsonEscape(const string& s){
    string out; out.reserve(s.size()+8);
    for(char c: s){
        switch(c){
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default: out += c; break;
        }
    }
    return out;
}

struct InputData {
    Point depot; int capacity{}; bool optimize{true}; vector<Pickup> pickups;
};

// Input format (lines via stdin):
// depot: lat,lng
// capacity: N
// optimize: 0|1
// pickup: name|lat|lng|demand
static bool parseInput(InputData& data){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string line;
    while (std::getline(cin, line)){
        if(line.empty()) continue;
        auto pos = line.find(":");
        if(pos==string::npos) continue;
        string key = line.substr(0,pos);
        string val = line.substr(pos+1);
        // trim spaces
        auto ltrim=[&](string &s){ s.erase(s.begin(), find_if(s.begin(), s.end(), [](unsigned char ch){return !isspace(ch);}));};
        auto rtrim=[&](string &s){ s.erase(find_if(s.rbegin(), s.rend(), [](unsigned char ch){return !isspace(ch);}).base(), s.end());};
        ltrim(key); rtrim(key); ltrim(val); rtrim(val);
        if(key=="depot"){
            double lat=0,lng=0; char c;
            replace(val.begin(), val.end(), '|', ',');
            stringstream ss(val); ss>>lat>>c>>lng; data.depot={lat,lng};
        } else if(key=="capacity"){
            data.capacity = stoi(val);
        } else if(key=="optimize"){
            data.optimize = (val!="0");
        } else if(key=="pickup"){
            // name|lat|lng|demand  (name may contain spaces but not pipes)
            string name; double lat=0,lng=0; int demand=0;
            // split by '|'
            vector<string> parts; parts.reserve(4);
            size_t start=0, p=0; 
            while((p=val.find('|', start))!=string::npos){ parts.emplace_back(val.substr(start, p-start)); start=p+1; }
            parts.emplace_back(val.substr(start));
            if(parts.size()>=4){
                name=parts[0];
                lat=stod(parts[1]); lng=stod(parts[2]); demand=stoi(parts[3]);
                Pickup pk{ name, {lat,lng}, demand, demand };
                data.pickups.push_back(std::move(pk));
            }
        }
    }
    return true;
}

static vector<vector<double>> buildTimeMatrix(const Point& depot, const vector<Pickup>& pks){
    size_t n = pks.size();
    vector<vector<double>> M(n+1, vector<double>(n+1, 0.0)); // 0=depot, 1..n pickups
    for(size_t i=0;i<=n;i++){
        for(size_t j=0;j<=n;j++){
            if(i==j){ M[i][j]=0.0; continue; }
            Point a = (i==0? depot : pks[i-1].p);
            Point b = (j==0? depot : pks[j-1].p);
            double m = haversineMeters(a,b);
            M[i][j] = metersToSeconds(m);
        }
    }
    return M;
}

static vector<vector<int>> solveVRPGreedy(const vector<vector<double>>& M, const vector<int>& demands, int capacity){
    int n = (int)demands.size();
    vector<int> remaining = demands;
    vector<vector<int>> trips;
    auto anyRemain=[&](){ for(int v: remaining) if(v>0) return true; return false; };
    while(anyRemain()){
        int capLeft = capacity;
        int cur = 0; // at depot
        vector<int> trip;
        while(capLeft>0 && anyRemain()){
            int best=-1; double bestT=numeric_limits<double>::infinity();
            for(int i=0;i<n;i++){
                if(remaining[i]<=0) continue;
                double t = M[cur][i+1];
                if(t < bestT){ bestT=t; best=i; }
            }
            if(best==-1 || !isfinite(bestT)) break;
            int take = min(remaining[best], capLeft);
            remaining[best]-=take; capLeft-=take;
            if(find(trip.begin(), trip.end(), best)==trip.end()) trip.push_back(best);
            cur = best+1;
        }
        if(!trip.empty()) trips.push_back(std::move(trip)); else break;
    }
    return trips;
}

static vector<vector<int>> splitTripsByCapacityInOrder(const vector<int>& demands, int capacity){
    int n=(int)demands.size();
    vector<int> rem=demands; vector<vector<int>> trips; vector<int> trip; int capLeft=capacity;
    for(int i=0;i<n;i++){
        while(rem[i]>0){
            if(capLeft==0){ if(!trip.empty()) trips.push_back(trip); trip.clear(); capLeft=capacity; }
            int take=min(rem[i], capLeft); rem[i]-=take; capLeft-=take;
            if(find(trip.begin(), trip.end(), i)==trip.end()) trip.push_back(i);
        }
    }
    if(!trip.empty()) trips.push_back(trip);
    return trips;
}

static TripInfo computeTripInfo(const Point& depot, const vector<Pickup>& pks, const vector<int>& idxs){
    TripInfo info; Point cur = depot;
    for(size_t k=0;k<idxs.size();k++){
        const Pickup& pk = pks[idxs[k]];
        double m = haversineMeters(cur, pk.p);
        double s = metersToSeconds(m);
        info.legs.push_back({pk.name, m, s});
        info.totalMeters += m; info.totalSeconds += s; cur = pk.p;
    }
    double backM = haversineMeters(cur, depot), backS = metersToSeconds(backM);
    info.backMeters = backM; info.backSeconds = backS;
    info.totalMeters += backM; info.totalSeconds += backS;
    return info;
}

int main(){
    InputData in; if(!parseInput(in)) return 1;
    // Prepare demands
    vector<int> demands; demands.reserve(in.pickups.size());
    for(const auto& p: in.pickups) demands.push_back(max(0, p.demand));
    // Build time matrix (Haversine/time approximation)
    auto M = buildTimeMatrix(in.depot, in.pickups);
    // Solve trips
    vector<vector<int>> trips = in.optimize ? solveVRPGreedy(M, demands, in.capacity)
                                            : splitTripsByCapacityInOrder(demands, in.capacity);
    // Output JSON
    cout << "{\n  \"trips\": [\n";
    for(size_t t=0;t<trips.size();t++){
        auto info = computeTripInfo(in.depot, in.pickups, trips[t]);
        cout << "    {\n";
        cout << "      \"items\": [\n";
        for(size_t k=0;k<info.legs.size();k++){
            const auto& L = info.legs[k];
            cout << "        {\"name\": \"" << jsonEscape(L.name) << "\", "
                 << "\"distanceText\": \"" << jsonEscape(fmtMiles(L.meters)) << "\", "
                 << "\"durationText\": \"" << jsonEscape(fmtMinutes(L.seconds)) << "\"}"
                 << (k+1<info.legs.size()? ",\n" : "\n");
        }
        cout << "      ],\n";
        cout << "      \"totalMeters\": " << (long long) llround(info.totalMeters) << ",\n";
        cout << "      \"totalSeconds\": " << (long long) llround(info.totalSeconds) << ",\n";
        cout << "      \"returnDistanceText\": \"" << jsonEscape(fmtMiles(info.backMeters)) << "\",\n";
        cout << "      \"returnDurationText\": \"" << jsonEscape(fmtMinutes(info.backSeconds)) << "\"\n";
        cout << "    }" << (t+1<trips.size()? ",\n" : "\n");
    }
    cout << "  ]\n}\n";
    return 0;
}

