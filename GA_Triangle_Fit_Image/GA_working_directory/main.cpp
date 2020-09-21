// 2020.9.19 ~ 2020.9.20
// 备注:
// 1. x正方向向下, y正方向向右, 这和numpy对Image对象的解读是一致的
// 2. 为了节省空间, 由于Pixel的rgb属于0~255, 考虑采用uint8_t
//      不过这样有点太拮据了, 而且有时候需要临时产生>255的值
//      因此改用 int16_t 作为 Pixel的rgb数据类型


#include<assert.h>      // assert()
#include<cmath>
#include<ctime>
#include<fstream>
#include<iostream>
#include<sys/stat.h>    // mkdir()
#include<unistd.h>      // usleep()
#include<vector>

using namespace std;





#define WORKING_DIRECTORY string("/Users/cuipy/Desktop/GA_working_directory/")  // 工作目录路径(最后要加上"/")
#define SAVE_INTERVAL 10                // 保存间隔, 每多少代保存一次
#define HEIGHT 200                      // 图片高度, 对应数组定义的第 1 个数字
#define WIDTH 300                       // 图片宽度, 对应数组定义的第 2 个数字

#define POPULATION 16                   // 每次迭代结束留下的个体数
#define MAX_ITERATION 5000              // 总迭代次数

#define TRIANGLE_AMOUNT 100             // 三角形的个数
#define FULLY_MUTATE_AMOUNT 1           // 彻底变异个数
#define SLIGHTLY_MUTATE_AMOUNT 3        // 轻微变异个数

#define FILTER_MIN 0.80                             // 滤光的通过率下限
#define FILTER_MAX 1.00                             // 滤光的通过率上限
#define POS_MUTATION_RANGE 0.03*min(WIDTH,HEIGHT)   // 轻微变异中坐标的变异幅度
#define RGB_MUTATION_RANGE 0.03                     // 轻微变异中滤波系数的变异幅度




class Pixel;
class Triangle;
void read_image(Pixel image[HEIGHT][WIDTH], string file_name);
void save_image(Pixel image[HEIGHT][WIDTH], string file_name);
inline int randint(int a, int b);
inline double uniform(double a, double b);
template<class T> inline void modify2fit(T& x, T a, T b);




// 形如 y = kx + b 的直线类
struct Line{
    double k;
    double b;
    Line(double k, double b) : k(k), b(b){}     // 利用k, b直接构造
    Line(int x1, int y1, int x2, int y2){       // 通过两个点来构造
        assert(x1 != x2);                       // 不应该出现对 x = a 类直线的计算!
        k = double(y2 - y1) / (x2 - x1);
        b = y1 - k * x1;
    }// 获取直线上与x对应的y坐标
    int at(int x){
        return int(k * x + b + 0.5);
    }
};


// 滤波参数类
struct Filter{
    // 表示"透过率" 属于(0, 1) 0表示这种光完全不能穿透, 1表示完全穿透
    double r, g, b;
    Filter(double r, double g, double b) : r(r), g(g), b(b){}
    Filter(){}
};


// 像素类
struct Pixel{
    int16_t r, g, b;    // 0 ~ 255
    Pixel(int16_t r = 255, int16_t g = 255, int16_t b = 255) : r(r), g(g), b(b){}
    void set_color(int16_t r_, int16_t g_, int16_t b_){
        this->r = r_; this->g = g_; this->b = b_;
    }
    void filted_by(Filter filter){
        r *= filter.r;
        g *= filter.g;
        b *= filter.b;
        modify2fit<int16_t>(r, 0, 255);
        modify2fit<int16_t>(g, 0, 255);
        modify2fit<int16_t>(b, 0, 255);
    }
};


// 功能: 在"图像(canvas)"上绘制一条水平"滤光线"
// transmissivity的三个分量是(0,1)之间的实数, 分别表示对rgb通道的透过率
inline void draw_horizontal_line(Pixel canvas[HEIGHT][WIDTH], int x, int y1, int y2, Filter filter){
    if(y1 > y2) {swap(y1, y2);}
    for(int i = y1; i <= y2; i++){
        canvas[x][i].filted_by(filter);
    }
}


// 三角形"滤光片"类
struct Triangle{
    int x0, y0;
    int x1, y1;
    int x2, y2;
    Filter filter;
    
    // 一般初始化
    Triangle(int x0, int y0, int x1, int y1, int x2, int y2, double r, double g, double b)
    : x0(x0), y0(y0), x1(x1), y1(y1), x2(x2), y2(y2), filter(r, g, b){}
    Triangle(){}    // 仅用于数组初始化!
    
    // 功能: 给定一个图像, 用当前三角形对该图像进行"滤波".
    void filt_image(Pixel canvas[HEIGHT][WIDTH]){
        // 首先对三个点冒泡排序 使:
        // xA ≤ xB ≤ xC
        int xA = x0, xB = x1, xC = x2;
        int yA = y0, yB = y1, yC = y2;
        if(xA > xB) {swap(xA, xB); swap(yA, yB);}
        if(xB > xC) {swap(xB, xC); swap(yB, yC);}
        if(xA > xB) {swap(xA, xB); swap(yA, yB);}
        // 对三角形的形状进行分类讨论:
        if(xA == xB && xB == xC){
            // 三点一线,不构成三角形
            return;
        }
        else if(xB == xC){
            //    A
            //    /\
            //   /  \
            // B ---- C
            Line AB(xA, yA, xB, yB);
            Line AC(xA, yA, xC, yC);
            for(int x = xA; x <= xB; x++){
                draw_horizontal_line(canvas, x, AB.at(x), AC.at(x), filter);
            }
        }
        else if(xA == xB){
            // A ---- B
            //   \  /
            //    \/
            //     C
            Line CA(xC, yC, xA, yA);
            Line CB(xC, yC, xB, yB);
            for(int x = xA; x <= xC; x++){
                draw_horizontal_line(canvas, x, CA.at(x), CB.at(x), filter);
            }
        }
        else{
            //    A
            //    /\
            // B /  \
            //   `--_\
            //        C
            Line AB(xA, yA, xB, yB);
            Line AC(xA, yA, xC, yC);
            Line BC(xB, yB, xC, yC);
            for(int x = xA; x <= xB; x++){
                draw_horizontal_line(canvas, x, AB.at(x), AC.at(x), filter);
            }
            for(int x = xB + 1; x <= xC; x++){
                draw_horizontal_line(canvas, x, BC.at(x), AC.at(x), filter);
            }
        }
    }
    
    // 以当前三角形为模板 进行轻微变异 返回新的三角形
    Triangle mutated(){
        // 先复制一份
        int nx0 = x0, ny0 = y0;
        int nx1 = x1, ny1 = y1;
        int nx2 = x2, ny2 = y2;
        double nr = filter.r;
        double ng = filter.g;
        double nb = filter.b;
        // 进行调整(注意是"+=")
        nx0 += randint(-POS_MUTATION_RANGE, POS_MUTATION_RANGE);
        ny0 += randint(-POS_MUTATION_RANGE, POS_MUTATION_RANGE);
        nx1 += randint(-POS_MUTATION_RANGE, POS_MUTATION_RANGE);
        ny1 += randint(-POS_MUTATION_RANGE, POS_MUTATION_RANGE);
        nx2 += randint(-POS_MUTATION_RANGE, POS_MUTATION_RANGE);
        ny2 += randint(-POS_MUTATION_RANGE, POS_MUTATION_RANGE);
        modify2fit<int>(nx0, 0, HEIGHT - 1);
        modify2fit<int>(ny0, 0, WIDTH - 1);
        modify2fit<int>(nx1, 0, HEIGHT - 1);
        modify2fit<int>(ny1, 0, WIDTH - 1);
        modify2fit<int>(nx2, 0, HEIGHT - 1);
        modify2fit<int>(ny2, 0, WIDTH - 1);
        nr += uniform(-RGB_MUTATION_RANGE, RGB_MUTATION_RANGE);
        ng += uniform(-RGB_MUTATION_RANGE, RGB_MUTATION_RANGE);
        nb += uniform(-RGB_MUTATION_RANGE, RGB_MUTATION_RANGE);
        modify2fit<double>(nr, FILTER_MIN, FILTER_MAX);
        modify2fit<double>(ng, FILTER_MIN, FILTER_MAX);
        modify2fit<double>(nb, FILTER_MIN, FILTER_MAX);
//        cout << x0 << " -> " << nx0 << endl;
//        cout << x1 << " -> " << nx1 << endl;
//        cout << x2 << " -> " << nx2 << endl;
//        cout << y0 << " -> " << ny0 << endl;
//        cout << y1 << " -> " << ny1 << endl;
//        cout << y2 << " -> " << ny2 << endl;
//        cout << filter.r << " -> " << nr << endl;
//        cout << filter.g << " -> " << ng << endl;
//        cout << filter.b << " -> " << nb << endl;
        return Triangle(nx0, ny0, nx1, ny1, nx2, ny2, nr, ng, nb);
    }
    
    // (静态方法) 从两个三角形中随机选一个
    static Triangle choice(const Triangle& t1, const Triangle& t2){
        return (rand() % 2) ? t1 : t2;
    }

};




// 个体类
struct Individual{
    static int64_t now_id;
    int64_t id;
    double diff;  // 与标准的差异, 越小越好
    Triangle triangles[TRIANGLE_AMOUNT];
    
    // 初始化方式1: 随机初始化
    Individual(){
        id = ++now_id;
        for(int i = 0; i < TRIANGLE_AMOUNT; i++){
            triangles[i] =  Triangle(
                     randint(0, HEIGHT), randint(0, WIDTH),
                     randint(0, HEIGHT), randint(0, WIDTH),
                     randint(0, HEIGHT), randint(0, WIDTH),
                     uniform(FILTER_MIN, FILTER_MAX),
                     uniform(FILTER_MIN, FILTER_MAX),
                     uniform(FILTER_MIN, FILTER_MAX)  );
        }
    }
    
    // 初始化方式2: 从父母随机继承三角形
    Individual(const Individual& p1, const Individual& p2){
        for(int i = 0; i < TRIANGLE_AMOUNT; i++){
            triangles[i] = Triangle::choice(p1.triangles[i], p2.triangles[i]);
        }
    }
    
    
    // 存储自己的三角形信息(图像矩阵 & 每个三角形的信息(UNDONE))
    void save_self_info(string as_name){
        Pixel canvas[HEIGHT][WIDTH];                // 新建一张纯白色画布
        for(int i = 0; i < TRIANGLE_AMOUNT; i++){   // 将自己的三角形作用于画布
            triangles[i].filt_image(canvas);
        }
        save_image(canvas, WORKING_DIRECTORY + "mat/" + as_name);   // 储存图片信息(int16_t矩阵)
        // 储存三角形信息(为.txt格式)
        ofstream fout(WORKING_DIRECTORY + "triangles/" + as_name + ".txt");
        for(int i = 0; i < TRIANGLE_AMOUNT; i++){
            fout << "((" << triangles[i].x0 << ", " << triangles[i].y0 << "), ";
            fout << "(" << triangles[i].x1 << ", " << triangles[i].y1 << "), ";
            fout << "(" << triangles[i].x2 << ", " << triangles[i].y2 << "), ";
            fout << "(" << triangles[i].filter.r << ", " << triangles[i].filter.g << ", ";
            fout << triangles[i].filter.b << ")), " << endl;
        }
        fout.close();
    }
    
    
    // 变异
    void mutate(){
        // 随机选 FULLY_MUTATE_AMOUNT 个三角形, 替换为全新的
        for(int i = 0; i < FULLY_MUTATE_AMOUNT; i++){
            triangles[rand() % TRIANGLE_AMOUNT]
                    = Triangle(
                    randint(0, HEIGHT), randint(0, WIDTH),
                    randint(0, HEIGHT), randint(0, WIDTH),
                    randint(0, HEIGHT), randint(0, WIDTH),
                    uniform(FILTER_MIN, FILTER_MAX),
                    uniform(FILTER_MIN, FILTER_MAX),
                    uniform(FILTER_MIN, FILTER_MAX)  );
        }
        // 随机选 SLIGHTLY_MUTATE_AMOUNT 个三角形, 轻微调整
        for(int i = 0; i < SLIGHTLY_MUTATE_AMOUNT; i++){
            int temp = rand();
            triangles[temp % TRIANGLE_AMOUNT] = triangles[temp % TRIANGLE_AMOUNT].mutated();
        }
    }
    
    
    // 计算自己和目标图片的"差距", 存储到 this->diff 中
    void calc_diff(Pixel TARGET[HEIGHT][WIDTH]){
        // 先绘制自己的图像
        Pixel canvas[HEIGHT][WIDTH];
        for(int i = 0; i < TRIANGLE_AMOUNT; i++){
            triangles[i].filt_image(canvas);
        }
        // 与目标图片进行比对
        int64_t variance = 0;
        for(int i = 0; i < HEIGHT; i++){
            for(int j = 0; j < WIDTH; j++){
                variance += (TARGET[i][j].r - canvas[i][j].r) * (TARGET[i][j].r - canvas[i][j].r);
                variance += (TARGET[i][j].g - canvas[i][j].g) * (TARGET[i][j].g - canvas[i][j].g);
                variance += (TARGET[i][j].b - canvas[i][j].b) * (TARGET[i][j].b - canvas[i][j].b);
            }
        }// 存储
        this->diff = sqrt(double(variance) / double(HEIGHT * WIDTH) / 3);
    }
    
    // 排序前请确保先调用calc_diff()
    bool operator < (const Individual& another) const{
        return this->diff < another.diff;
    }
    
};
int64_t Individual::now_id = 0;







int main(){

    // 设置随机种子
    srand((unsigned)time(NULL));
    
    // 在工作路径下创建文件夹
    mkdir((WORKING_DIRECTORY + "mat/").c_str(), S_IRWXU);
    mkdir((WORKING_DIRECTORY + "imaged/").c_str(), S_IRWXU);
    mkdir((WORKING_DIRECTORY + "triangles/").c_str(), S_IRWXU);
    
    
    
    // 读取目标图片
    Pixel TARGET_IMAGE[HEIGHT][WIDTH];
    read_image(TARGET_IMAGE, WORKING_DIRECTORY + "target_image.dat");

    // 创建最初的 POPULATION 个随机个体
    Individual::now_id = 0;
    vector<Individual> population;
    for(int i = 0; i < POPULATION; i++){
        population.push_back(Individual());
    }
    
    // 开始迭代
    int64_t generation = -1;
    while(generation++ != MAX_ITERATION){
        cout << "第" << generation << "代开始运算..." << endl;
        // 两两交叉, 创建遗传个体
        for(int i = 0; i < POPULATION; i++){
            for(int j = i + 1; j < POPULATION; j++){
                population.push_back(Individual(population[i], population[j]));
            }
        }
        // 对新产生的个体进行变异
        for(auto ind = population.begin() + POPULATION; ind != population.end(); ind++){
            ind->mutate();
        }
        // 对当前所有个体计算diff
        for(auto& ind: population){
            ind.calc_diff(TARGET_IMAGE);
        }
        // 对当前所有个体排序
        sort(population.begin(), population.end());

        // 舍弃末尾个体
        population.resize(POPULATION);

        // 保存这一代的最优个体, 并输出这一代存活的个体中, 最好的 & 最差的 分别的 diff 值
        if(generation % SAVE_INTERVAL == 0){
            population.begin()->save_self_info(to_string(generation));
        }
        cout << population.begin()->diff <<" <--> " << population.rbegin()->diff<< endl;
    
    }


    

    
    
    return 0;
}




//从文件中读取目标图片(的矩阵[HEIGHT][WIDTH][0,1,2,3], 但我们只取[0,1,2], 舍弃[3](alpha)通道)
void read_image(Pixel image[HEIGHT][WIDTH], string file_name){
    ifstream fin(file_name, ios::in|ios::binary);
    int16_t temp0, temp1, temp2, temp3;
    for(int i = 0; i < HEIGHT; i++){
        for(int j = 0; j < WIDTH; j++){
            fin.read((char*)& temp0, sizeof(int16_t));
            fin.read((char*)& temp1, sizeof(int16_t));
            fin.read((char*)& temp2, sizeof(int16_t));
            fin.read((char*)& temp3, sizeof(int16_t));
            image[i][j].set_color(temp0, temp1, temp2);
        }
    }
    fin.close();
}


// 将矩阵输出为numpy可以读取的格式(int16)
void save_image(Pixel image[HEIGHT][WIDTH], string file_name){
    ofstream fout(file_name, ios::out|ios::binary);
    int16_t alpha = 255;
    for(int i = 0; i < HEIGHT; i++){
        for(int j = 0; j < WIDTH; j++){
            fout.write((const char*)(&(image[i][j].r)), sizeof(int16_t));
            fout.write((const char*)(&(image[i][j].g)), sizeof(int16_t));
            fout.write((const char*)(&(image[i][j].b)), sizeof(int16_t));
            fout.write((const char*)(&alpha), sizeof(int16_t));
        }
    }
    fout.close();
}

// 生成随机整数 of [a, b)
inline int randint(int a, int b){
    return rand() % (b - a) + a;
}
// 生成随机浮点数 of [a, b)
inline double uniform(double a, double b){
    return rand() * 1.0 / RAND_MAX * (b - a) + a;
}
// 限制一个数,使之≥a, 且≤b
template<class T>
inline void modify2fit(T& x, T a, T b){
    if(x > b){
        x = b;
    }
    else if(x < a){
        x = a;
    }
}
