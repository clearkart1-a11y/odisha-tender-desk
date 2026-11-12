"""Map messy tender location strings (+ pincode) to one of Odisha's 30 districts."""
import re, collections as C
DIST = {
 'Angul':['angul','anugul','talcher','talacher','athmallik','pallahara','chhendipada','banarpal','kaniha','kishorenagar'],
 'Balangir':['balangir','bolangir','titilagarh','titlagarh','kantabanji','patnagarh','saintala','tusura','belpada','loisingha','muribahal','agalpur','bangomunda','tureikela','puintala','deogaon'],
 'Balasore':['balasore','baleswar','baleshwar','jaleswar','nilgiri','soro','basta','remuna','simulia','oupada','bahanaga','khaira','baliapal','bhograi'],
 'Bargarh':['bargarh','baragarh','barpali','padampur','attabira','bijepur','sohela','bheden','paikmal','ambabhona','bhatli','gaisilet','jharbandh','rajborasambar'],
 'Bhadrak':['bhadrak','basudevpur','chandbali','dhamnagar','dhamanagar','tihidi','bhandaripokhari','akhuapada','bant '],
 'Boudh':['boudh','baudh','kantamal','harbhanga'],
 'Cuttack':['cuttack','athgarh','banki','badamba','narasinghpur','salepur','niali','mahanga','choudwar','nischintakoili','kantapada','baranga','tigiria'],
 'Deogarh':['deogarh','debagarh','reamal','tileibani','barkote'],
 'Dhenkanal':['dhenkanal','kamakhyanagar','bhuban','hindol','gondia','parjang','odapada'],
 'Gajapati':['gajapati','paralakhemundi','parlakhemundi','mohana','kashinagar','r.udayagiri','r udayagiri','gumma','nuagada','adava'],
 'Ganjam':['ganjam','berhampur','brahmapur','aska','bhanjanagar','chhatrapur','chatrapur','hinjili','hinjilicut','digapahandi','polasara','kodala','khallikote','gopalpur','purushottampur','buguda','sorada','patrapur','badagada','dharakote','jagannathprasad','kabisuryanagar','rangeilunda','sanakhemundi','belaguntha','beguniapada','sheragada','chikiti','kukudakhandi','ganjam'],
 'Jagatsinghpur':['jagatsinghpur','jagatsingpur','paradip','paradeep','tirtol','kujang','erasama','balikuda','raghunathpur','biridi','naugaon'],
 'Jajpur':['jajpur','vyasanagar','jaraka','binjharpur','dharmasala','korei','sukinda','danagadi','badachana','rasulpur','dasarathpur','kuakhia','panikoili'],
 'Jharsuguda':['jharsuguda','brajarajnagar','belpahar','lakhanpur','kolabira','laikera','kirmira'],
 'Kalahandi':['kalahandi','bhawanipatna','dharmagarh','dharamgarh','junagarh','kesinga','lanjigarh','th.rampur','th rampur','thuamul','golamunda','jaipatna','koksara','karlamunda','madanpur','narla','kalampur'],
 'Kandhamal':['kandhamal','phulbani','balliguda','baliguda','g.udayagiri','g udayagiri','tikabali','daringbadi','raikia','kotagarh','tumudibandh','phiringia','chakapada','k.nuagaon'],
 'Kendrapara':['kendrapara','kendrapada','kendrapda','pattamundai','pattamu','aul ','rajnagar','marshaghai','rajkanika','mahakalapada','derabish','garadpur'],
 'Keonjhar':['keonjhar','kendujhar','kenojhar','salapada','anandapur','ghatagaon','champua','barbil','badabil','joda','harichandanpur','telkoi','hatadihi','ghasipura','saharpada','jhumpura','kanupur'],
 'Khordha':['khordha','khurda','khurdha','bhubaneswar','bbsr','balianta','jatni','banapur','balugaon','begunia','bolagarh','chilika','balipatna'],
 'Koraput':['koraput','jeypore','sunabeda','kotpad','semiliguda','lamtaput','nandapur','borigumma','dasamantapur','pottangi','boipariguda','damanjodi'],
 'Malkangiri':['malkangiri','mathili','kalimela','korukonda','chitrakonda','podia','khairput'],
 'Mayurbhanj':['mayurbhanj','baripada','udala','rairangpur','karanjia','betnoti','kaptipada','jashipur','bangiriposi','morada','badasahi','khunta','thakurmunda','kusumi','tiring','bisoi','saraskana','rasgovindpur','bahalda','jamda','suliapada','samakhunta'],
 'Nabarangpur':['nabarangpur','nabarangapur','nowrangpur','umerkote','raighar','papadahandi','papdahandi','kosagumuda','tentulikhunti','jharigam','chandahandi','nandahandi','dabugam'],
 'Nayagarh':['nayagarh','odagaon','daspalla','dasapalla','khandapada','ranpur','bhapur','gania'],
 'Nuapada':['nuapada','khariar','komna','sinapali','boden','komana'],
 'Puri':['puri','nimapara','pipili','konark','kakatpur','satyabadi','delanga','gop ','astaranga','brahmagiri','krushnaprasad','kanas','sakhigopal'],
 'Rayagada':['rayagada','gunupur','bissam','muniguda','kashipur','kalyansinghpur','gudari','chandrapur','ramanaguda','kolnara'],
 'Sambalpur':['sambalpur','burla','hirakud','kuchinda','rengali','rairakhol','redhakhol','jamankira','maneswar','dhankauda','jujumura','naktideul','bamra'],
 'Subarnapur':['subarnapur','sonepur','sonapur','binka','tarbha','birmaharajpur','ullunda','dunguripali'],
 'Sundargarh':['sundargarh','rourkela','bonai','rajgangpur','biramitrapur','koida','lahunipara','kuarmunda','lathikata','bisra','hemgir','tangarpali','bargaon'],
}
KEYS = sorted(((k, d) for d, ks in DIST.items() for k in ks), key=lambda x: -len(x[0]))

def by_text(s):
    s = ' ' + (s or '').lower() + ' '
    for k, d in KEYS:
        if k in s: return d
    return None

def build(rows):
    """rows: list of (loc, pin, extra_text). Returns list of district or ''"""
    first = [by_text(l) or by_text(x) for l, p, x in rows]
    p6, p3 = C.defaultdict(C.Counter), C.defaultdict(C.Counter)
    for (l, p, x), d in zip(rows, first):
        p = re.sub(r'\D', '', str(p or ''))
        if d and len(p) == 6: p6[p][d] += 1; p3[p[:3]][d] += 1
    out = []
    for (l, p, x), d in zip(rows, first):
        if not d:
            p = re.sub(r'\D', '', str(p or ''))
            if p in p6: d = p6[p].most_common(1)[0][0]
            elif p[:3] in p3 and p3[p[:3]].most_common(1)[0][1] >= 5: d = p3[p[:3]].most_common(1)[0][0]
        out.append(d or '')
    return out
