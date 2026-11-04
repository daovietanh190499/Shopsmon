"""Tech news items for /news/. Every item was checked against the linked source (WebSearch, 2026-11-04).
Facts are attributed to the source; company figures are marked as the company's / source's own claims.
Newest first. Fields: date, cat (key), src (display name), url, title{vi,en}, body{vi,en}.
"""

CATS = {
    "ai": {"vi": "AI & LLM", "en": "AI & LLM"},
    "cs": {"vi": "Khoa học máy tính & dữ liệu", "en": "Computer science & data"},
    "hw": {"vi": "Hệ thống máy tính & chip", "en": "Computer systems & chips"},
    "mobile": {"vi": "Điện thoại & mạng di động", "en": "Smartphones & mobile networks"},
    "iot": {"vi": "IoT & AIoT", "en": "IoT & AIoT"},
}

NEWS = [
    dict(date="2026-11-03", cat="iot", src="IoT Now",
         url="https://iot-now.com/2026/11/03/159158-ceva-mobilint-physical-ai-regulus-edge-ai-soc/",
         title={"vi": "Ceva và Mobilint: SoC edge AI REGULUS đạt 10 TOPS dưới 3 W cho robot, drone và thiết bị IoT",
                "en": "Ceva and Mobilint: the REGULUS edge-AI SoC delivers 10 TOPS under 3 W for robots, drones and IoT"},
         body={"vi": "Theo IoT Now, Ceva thông báo Mobilint đã đưa SensPro AI DSP và NeuPro-Nano NPU của Ceva vào SoC REGULUS &mdash; lần triển khai sản xuất đầu tiên của dòng NPU NeuPro. Hãng cho biết REGULUS đạt 10 TOPS ở mức dưới 3 W, hỗ trợ tới 8 GB bộ nhớ, nhắm tới robot, drone, thị giác máy, camera thông minh và thiết bị IoT. Bộ tăng tốc USB MLD-R1 dựa trên REGULUS (giới thiệu tại COMPUTEX 2026) đã bắt đầu giao hàng, hỗ trợ PyTorch, ONNX, Hugging Face, TensorFlow, TFLite và Keras. Các con số hiệu năng là của nhà sản xuất.",
               "en": "According to IoT Now, Ceva announced that Mobilint has deployed Ceva's SensPro AI DSP and NeuPro-Nano NPU in its REGULUS SoC &mdash; the first production deployment of the NeuPro NPU family. The company says REGULUS delivers 10 TOPS at under 3 W with up to 8 GB of memory, aimed at robotics, drones, machine vision, smart cameras and IoT devices. The REGULUS-based MLD-R1 USB accelerator (previewed at COMPUTEX 2026) is now shipping, with support for PyTorch, ONNX, Hugging Face, TensorFlow, TFLite and Keras. Performance figures are the manufacturer's."}),
    dict(date="2026-11-03", cat="iot", src="New Electronics",
         url="https://www.newelectronics.co.uk/content/news/brainchip-introduces-akd1500-raspberry-pi-5-development-kit-for-edge-ai-applications",
         title={"vi": "BrainChip ra bộ kit AKD1500 trên Raspberry Pi 5 cho AI công suất thấp, luôn bật",
                "en": "BrainChip launches an AKD1500 Raspberry Pi 5 kit for low-power, always-on AI"},
         body={"vi": "Theo New Electronics, BrainChip giới thiệu bộ kit phát triển gồm Raspberry Pi 5 và bo mạch tăng tốc M.2 AKD1500. Chip AKD1500 dùng kiến trúc neuromorphic hướng sự kiện: theo hãng, nó chỉ xử lý các sự kiện đáng kể thay vì phân tích mọi điểm dữ liệu nên giảm điện năng khi cần giám sát liên tục, và hỗ trợ học ngay trên thiết bị để cập nhật mô hình tại hiện trường mà không cần huấn luyện lại trên cloud. Hãng nhấn mạnh cùng con chip dùng khi phát triển có thể đưa vào sản phẩm cuối. Mức tiết kiệm năng lượng là tuyên bố của hãng, chưa có đo kiểm độc lập trong bài.",
               "en": "According to New Electronics, BrainChip introduced a development kit that pairs a Raspberry Pi 5 with the AKD1500 M.2 accelerator board. The AKD1500 uses an event-driven neuromorphic architecture: the company says it processes only significant events rather than every data point, cutting energy use for always-on monitoring, and supports on-device learning so models can be updated in the field without cloud retraining. BrainChip stresses that the same chip used in development can go into the final product. The energy savings are the company's claim; the article reports no independent measurements."}),
    dict(date="2026-11-03", cat="iot", src="Matter Alpha / matter.js",
         url="https://www.matteralpha.com/industry-news/home-assistant-s-matter-server-adds-matter-1-6-1-camera-talkback-ikea-aqara-fp400-support",
         title={"vi": "Matter 1.6.1 đến với Home Assistant: Groupcast, camera hai chiều và nền tảng matter.js 0.18",
                "en": "Matter 1.6.1 reaches Home Assistant: Groupcast, two-way camera audio and the matter.js 0.18 engine"},
         body={"vi": "Theo Matter Alpha, Connectivity Standards Alliance phát hành Matter 1.6.1 hồi tháng 9: Groupcast thoát trạng thái thử nghiệm và chuông cửa có điều khiển âm lượng/tắt tiếng riêng. Home Assistant hiện gửi lệnh nhóm thiết bị bằng chuỗi lệnh unicast lần lượt (hiệu ứng đèn sáng so le); Groupcast tạo nền tảng cho thông điệp multicast IPv6 qua Thread, Wi-Fi và Ethernet. matter.js 0.18.0 (20/10) hỗ trợ Matter 1.6.1, và Matter Server cho Home Assistant đang nâng lên engine này, kèm API camera WebRTC và hỗ trợ thiết bị Aqara, IKEA. Một điểm cần lưu ý: người dùng chỉ hưởng lợi khi chính thiết bị cũng hỗ trợ phiên bản mới.",
               "en": "According to Matter Alpha, the Connectivity Standards Alliance released Matter 1.6.1 in September: Groupcast graduated from provisional status and doorbell chimes gained independent volume and mute controls. Home Assistant currently sends group commands as sequential unicast messages (the staggered &ldquo;popcorn&rdquo; lighting effect); Groupcast lays the groundwork for IPv6 multicast group messaging over Thread, Wi-Fi and Ethernet. matter.js 0.18.0 (Oct 20) supports Matter 1.6.1, and the Matter Server for Home Assistant is moving to that engine, with a WebRTC camera API and new Aqara and IKEA support. One caveat: users only benefit once their devices also support the new version."}),
    dict(date="2026-11-03", cat="ai", src="arXiv",
         url="https://arxiv.org/abs/2611.02332",
         title={"vi": "LeanGuard: kiểm tra từng lệnh gọi công cụ của agent LLM bằng chính sách viết trong Lean 4",
                "en": "LeanGuard: checking every tool call of an LLM agent against a policy written in Lean 4"},
         body={"vi": "Nhóm tác giả (Sankar, Ganguly, Singh và cộng sự) đề xuất LeanGuard, một runtime kiểm tra mọi lệnh gọi công cụ mà agent đề xuất theo chính sách viết bằng Lean 4 trước khi lệnh tới môi trường; hệ thống từ chối mặc định (fail-closed). Trên Tau-Bench với năm mô hình Qwen (0,8B&ndash;27B), các agent không có bảo vệ thực thi ít nhất 33 lệnh mà chính sách cấm, còn LeanGuard thực thi 0 lệnh; trên DTap, tỉ lệ prompt-injection trực tiếp thành công giảm từ 57,9% xuống 5,9%. Với các lệnh bị từ chối do giá trị tham số, cơ chế sửa có chứng minh tìm được bản chỉnh hợp lệ cho 88 trên 252 trường hợp. Đây là kết quả do chính các tác giả công bố trong bản preprint arXiv.",
               "en": "The authors (Sankar, Ganguly, Singh and colleagues) propose LeanGuard, a runtime that checks every tool call an agent proposes against a policy written in Lean 4 before it reaches the environment; evaluation is fail-closed. On Tau-Bench with five Qwen models (0.8B&ndash;27B), unguarded agents executed at least 33 calls the policy forbids while LeanGuard executed none; on DTap, direct prompt-injection success fell from 57.9% to 5.9%. For calls denied because of argument values, proof-guided repair found an admissible edit for 88 of 252 denials. These are the authors' own results from the arXiv preprint."}),
    dict(date="2026-11-03", cat="ai", src="arXiv",
         url="https://arxiv.org/abs/2611.03618",
         title={"vi": "Strategist: meta-agent tự tiến hoá chiến lược suy luận dưới dạng mã, giảm 39% chi phí suy luận",
                "en": "Strategist: a meta-agent that evolves inference strategies as code, with 39% lower inference cost"},
         body={"vi": "Lu, Xu, Hua và Liu giới thiệu Strategist, một meta-agent viết chiến lược suy luận thành &ldquo;blueprint&rdquo; &mdash; mã thực thi mà các chiến lược khác tái sử dụng &mdash; rồi lưu vào một thư viện. Với mỗi tác vụ và một tập phát triển nhỏ, hệ thống truy xuất blueprint liên quan, viết chiến lược ứng viên, thử trên mẫu thật và sửa theo kết quả. Theo tóm tắt của tác giả, trên 30 benchmark Strategist vượt baseline mạnh nhất ở 24 benchmark; độ chính xác trung bình 74,7% so với 74,0% với chi phí suy luận thấp hơn 39%, và các chiến lược chuyển được sang tác vụ và mô hình chưa gặp mà không cần tìm kiếm lại. Kết quả là của nhóm tác giả, chưa có kiểm chứng độc lập.",
               "en": "Lu, Xu, Hua and Liu introduce Strategist, a meta-agent that writes inference strategies as &ldquo;blueprints&rdquo; &mdash; executable code that other strategies can reuse &mdash; and stores them in a library. For a given task and a small development set, it retrieves related blueprints, writes candidate strategies, tests them on real samples and revises them from the results. According to the authors' abstract, across 30 benchmarks Strategist beats the strongest baseline on 24; average accuracy is 74.7% vs 74.0% at 39% lower inference cost, and strategies transfer to unseen tasks and other models without further search. The results are the authors' own, without independent verification."}),
    dict(date="2026-11-03", cat="ai", src="Google DeepMind",
         url="https://deepmind.google/blog/agentic-cheminformatics-with-google-antigravity/",
         title={"vi": "DeepMind: agent AI rút ngắn quy trình thiết kế thuốc xuống còn khoảng một giờ",
                "en": "DeepMind: an AI agent compresses a drug-design iteration to about an hour"},
         body={"vi": "Google DeepMind giới thiệu bộ \"Cheminformatics Skills\" cho Google Antigravity. Trên dữ liệu thật về thuốc điều trị ung thư phổi, agent tìm trong hàng nghìn hợp chất, phân tích cặp phân tử tương đồng (MMPA) và đề xuất macrocycle mới kèm lộ trình tổng hợp trong khoảng một giờ &mdash; vốn thường mất nhiều ngày cho một vòng lặp. Chính DeepMind lưu ý các thiết kế chỉ là giả thuyết cần được tổng hợp và kiểm chứng thực nghiệm.",
               "en": "Google DeepMind introduced \"Cheminformatics Skills\" for Google Antigravity. On real lung-cancer drug data, the agent searches thousands of compounds, runs matched molecular pair analysis (MMPA) and proposes novel macrocycles with synthetic routes in about an hour &mdash; a loop that typically takes several days. DeepMind itself cautions that the designs are testable hypotheses that must still be synthesised and validated experimentally."}),
    dict(date="2026-11-03", cat="hw", src="Futurum Group",
         url="https://futurumgroup.com/insights/qualcomm-validates-first-hbc-silicon-with-an-18x-memory-bandwidth-gain-over-lpddr5x/",
         title={"vi": "Qualcomm xác nhận silicon HBC đầu tiên: băng thông bộ nhớ gấp 18 lần LPDDR",
                "en": "Qualcomm validates first HBC silicon: 18x memory bandwidth over LPDDR"},
         body={"vi": "Theo Futurum, Qualcomm đã kiểm chứng trong phòng lab công nghệ High Bandwidth Compute (HBC): một mẫu DRAM xếp hai lớp gắn trên die tính toán đo được băng thông gấp 18 lần LPDDR và hiệu quả băng thông/watt gấp 5 lần HBM4. Qualcomm chưa công bố workload, mô hình hay độ chính xác dùng khi đo, nên đây là kết quả của một kernel thành phần chứ chưa phải suy luận đầu-cuối. Dragonfly AI250 (nền tảng đầu tiên dùng HBC) dự kiến gửi mẫu cho khách hàng trong nửa đầu 2027.",
               "en": "According to Futurum, Qualcomm has validated its High Bandwidth Compute (HBC) technology in the lab: a two-layer stacked-DRAM sample bonded to a compute die measured 18x the bandwidth of LPDDR and 5x the bandwidth per watt of HBM4. Qualcomm did not disclose the workload, model or precision, so this is a component-kernel result rather than end-to-end inference. The Dragonfly AI250, the first HBC platform, is due to sample to customers in the first half of 2027."}),
    dict(date="2026-11-03", cat="iot", src="Nordic Semiconductor",
         url="https://www.nordicsemi.com/Nordic-news/2026/11/Nordic-brings-edge-AI-to-battery-powered-WiFi-devices-20-times-lower-standby-power-with-nRF71-Series",
         title={"vi": "Nordic nRF71: Wi-Fi, Bluetooth LE, Thread và edge AI trên một chip, tiết kiệm điện chờ tới 20 lần",
                "en": "Nordic nRF71: Wi-Fi, Bluetooth LE, Thread and edge AI on one chip, up to 20x lower standby power"},
         body={"vi": "Nordic Semiconductor công bố dòng SoC nRF71 (nRF7120 với Wi-Fi 6 hai băng tần, nRF7120E thêm Wi-Fi 6E). Hãng cho biết công suất chờ thấp hơn tới 20 lần so với dòng nRF70 hiện tại, và NPU Axon tích hợp chạy mô hình ML nhanh hơn 10&ndash;17 lần so với lõi Cortex-M33 256 MHz đứng một mình &mdash; đủ cho nhận diện từ khoá, phát hiện bất thường, phân loại ảnh trên thiết bị chạy pin. Các con số là của nhà sản xuất; chip đang gửi mẫu.",
               "en": "Nordic Semiconductor announced the nRF71 SoC series (nRF7120 with dual-band Wi-Fi 6, nRF7120E adding tri-band Wi-Fi 6E). The company says standby power is up to 20x lower than the current nRF70 series, and the integrated Axon NPU runs ML models 10&ndash;17x faster than the 256 MHz Cortex-M33 alone &mdash; enough for keyword spotting, anomaly detection and image classification on battery-powered devices. Figures are the manufacturer's; the chips are sampling."}),
    dict(date="2026-11-02", cat="cs", src="KAIST",
         url="https://pr.kaist.ac.kr/newsen/html/news/?mng_no=68990&mode=V",
         title={"vi": "KAIST: CluSTER rút ngắn thời gian fine-tune LLM tới 69,6% mà giữ gần nguyên chất lượng",
                "en": "KAIST: CluSTER cuts LLM fine-tuning time by up to 69.6% with nearly the same quality"},
         body={"vi": "Nhóm của GS. Jae-Gil Lee (KAIST) đề xuất CluSTER: gom và chọn dữ liệu có tác dụng học tương tự nhau rồi chia đều cho nhiều GPU để giảm việc học lặp. Trên mô hình ~7B và 13B với ba bộ dữ liệu lập trình/y khoa và tám benchmark, mô hình giữ gần như cùng hiệu năng khi chỉ dùng khoảng 31% dữ liệu, thời gian huấn luyện giảm tới 69,6% (10 giờ còn khoảng 3 giờ). Thí nghiệm chủ yếu trên 4 GPU, công bố tại EMNLP 2026.",
               "en": "Professor Jae-Gil Lee's team at KAIST proposes CluSTER, which groups and selects data with similar learning effect and spreads it evenly over multiple GPUs to reduce repeated learning. On ~7B and 13B models, three coding/medical datasets and eight benchmarks, models kept nearly the same performance with only about 31% of the data while training time dropped by up to 69.6% (10 hours to about 3). Experiments were mainly on 4 GPUs; presented at EMNLP 2026."}),
    dict(date="2026-11-02", cat="cs", src="UCL",
         url="https://www.ucl.ac.uk/mathematical-physical-sciences/high-energy-physics/reconstruct-everything-ucls-pioneering-ai-model-could-redefine-particle-physics-reconstruction",
         title={"vi": "UCL: mô hình AI \"REM\" tái tạo toàn bộ va chạm hạt, hiệu suất từ 61% lên 92% (trên mô phỏng)",
                "en": "UCL: the \"REM\" AI model reconstructs entire particle collisions, efficiency 61% to 92% (in simulation)"},
         body={"vi": "Các nhà nghiên cứu UCL xây dựng Reconstruct Everything Model (REM), khung học máy thống nhất tái tạo hạt trực tiếp từ phép đo của mọi hệ thống detector, thay cho chuỗi thuật toán chuyên biệt truyền thống. Trên mô phỏng chi tiết một detector đề xuất cho Future Circular Collider của CERN, hiệu suất tái tạo tăng từ 61% lên 92%, độ phân giải năng lượng jet cải thiện 52%, và một va chạm được tái tạo trong khoảng 30 ms trên một GPU. Kết quả là trên dữ liệu mô phỏng, chưa phải dữ liệu thực từ máy gia tốc.",
               "en": "UCL researchers built the Reconstruct Everything Model (REM), a unified machine-learning framework that reconstructs particles directly from measurements across all detector systems, replacing the traditional chain of specialised algorithms. On a detailed simulation of a detector proposed for CERN's Future Circular Collider, reconstruction efficiency rose from 61% to 92%, jet energy resolution improved by 52%, and a full collision is reconstructed in about 30 ms on a single GPU. These results are on simulated data, not real collider data."}),
    dict(date="2026-11-02", cat="ai", src="Zyphra",
         url="https://www.zyphra.com/our-work/zyphra-hierarchical-attention",
         title={"vi": "Zyphra ZHA: attention thưa phân cấp có độ phức tạp dưới bậc hai cho ngữ cảnh dài",
                "en": "Zyphra ZHA: hierarchical sparse attention with subquadratic complexity for long context"},
         body={"vi": "Zyphra giới thiệu Hierarchical Attention (ZHA): xây một cây phân cấp và tìm trên cây để chọn các token liên quan cho mỗi truy vấn, đạt độ phức tạp dưới bậc hai. Mô hình có sẵn được chuyển sang ZHA bằng một pha chưng cất chỉ vài tỷ token. Theo Zyphra, trên RULER-13 ở 256K token bản cây rộng đạt 96,2% (mô hình dày gốc 96,0%); trên LongBench v2 bản cây sâu đạt 63,4% so với 58,0% của attention dày khi chỉ attend ~1,1% KV cache lúc giải mã. Đây là kết quả do chính nhóm tác giả công bố.",
               "en": "Zyphra introduced Hierarchical Attention (ZHA), which builds a hierarchical tree and searches it to select the relevant tokens for each query, reaching subquadratic complexity. Existing pretrained models are adapted with a distillation phase of only a few billion tokens. Per Zyphra, on RULER-13 at 256K tokens the wide-tree model scores 96.2% (96.0% for the original dense model); on LongBench v2 the deep-tree model scores 63.4% vs 58.0% for dense attention while attending to ~1.1% of the KV cache during decoding. These are the authors' own reported results."}),
    dict(date="2026-11-02", cat="mobile", src="MediaTek",
         url="https://www.mediatek.com/press-room",
         title={"vi": "MediaTek và Ericsson: kết nối pre-6G đa nhà cung cấp đầu tiên, tải xuống tiềm năng >5 Gbps",
                "en": "MediaTek and Ericsson: first multi-vendor pre-6G over-the-air connection, >5 Gbps peak download potential"},
         body={"vi": "MediaTek cùng Ericsson công bố hoàn thành kết nối pre-6G over-the-air đa nhà cung cấp đầu tiên với băng thông kênh 400 MHz, thực hiện hồi tháng 9 tại T-Mobile 6G Innovation Hub (Bellevue). Hãng cho biết thử nghiệm cho thấy tiềm năng tốc độ tải xuống đỉnh trên 5 Gbps và tải lên trên 2 Gbps. Đây là thử nghiệm thực địa tiền-6G, chưa phải dịch vụ thương mại.",
               "en": "MediaTek and Ericsson announced the first multi-vendor pre-6G over-the-air connection using a 400 MHz channel bandwidth, carried out in September at the T-Mobile 6G Innovation Hub in Bellevue. The companies say it demonstrates potential peak download speeds above 5 Gbps and upload above 2 Gbps. It is a pre-6G field trial, not a commercial service."}),
    dict(date="2026-11-02", cat="mobile", src="Android Authority",
         url="https://www.androidauthority.com/motorola-signature-display-camera-specs-revealed-3730578/",
         title={"vi": "Motorola Signature 27 ra mắt toàn cầu 5/11: màn hình Tandem OLED tới 12.000 nit, camera tele 200MP",
                "en": "Motorola Signature 27 launches globally Nov 5: Tandem OLED up to 12,000 nits, 200MP telephoto"},
         body={"vi": "Theo Android Authority, Motorola đã xác nhận một phần thông số chính thức: màn hình 6,8 inch Tandem OLED với độ sáng công bố 12.000 nit (Galaxy S26 Ultra khoảng 2.600 nit theo bài viết), camera chính 50MP Sony LYT-910 có LOFIC, tele 200MP và siêu rộng 50MP, chạy Android 17 và hứa hẹn 7 năm cập nhật phần mềm. Pin, tốc độ sạc và giá chỉ được công bố tại sự kiện; giá đồn đoán không phải thông tin chính thức. Độ sáng và khả năng zoom là số liệu do hãng tuyên bố, chưa có đánh giá độc lập.",
               "en": "Per Android Authority, Motorola has officially confirmed some key specs: a 6.8-inch Tandem OLED display with a claimed 12,000 nits (the article puts the Galaxy S26 Ultra at about 2,600 nits), a 50MP Sony LYT-910 main camera with LOFIC, a 200MP telephoto and a 50MP ultrawide, Android 17 and a promise of seven years of software updates. Battery, charging speed and price will only be revealed at launch; rumoured prices are not official. Brightness and zoom figures are the company's claims, not independently tested."}),
    dict(date="2026-10-29", cat="ai", src="Bad Influence (AI Weekly)",
         url="https://badinfluence.news/weekly",
         title={"vi": "Mistral mở trọng số Mistral Large 4: mô hình đa phương thức 1 nghìn tỷ tham số",
                "en": "Mistral releases open weights for Mistral Large 4: a 1-trillion-parameter multimodal model"},
         body={"vi": "Theo bản tin AI Weekly của Bad Influence, Mistral AI đã công bố trọng số của phiên bản Mistral Large 4 cải tiến sau ba tuần học tăng cường bổ sung &mdash; mô hình đa phương thức 1T tham số, giấy phép MIT có chỉnh sửa. Hãng báo cáo 51% trên Artificial Analysis Cyber Index và 41% trên Terminal-Bench 4.0 (tăng 13 điểm so với bản xem trước); API giá $0,70 / $2,10 mỗi triệu token vào / ra. Cùng tuần, vLLM thông báo hỗ trợ ngay ngày đầu (mô hình MoE, 49 tỷ tham số hoạt động mỗi token). Số liệu benchmark là do hãng báo cáo.",
               "en": "According to Bad Influence's AI Weekly, Mistral AI released the open weights of an improved Mistral Large 4 after three more weeks of reinforcement learning &mdash; a 1T-parameter multimodal model under a modified MIT licence. The company reports 51% on the Artificial Analysis Cyber Index and 41% on Terminal-Bench 4.0 (up 13 points over the public preview); API pricing is $0.70 / $2.10 per million input / output tokens. The same week vLLM announced day-0 support (a mixture-of-experts model with 49B active parameters per token). Benchmark figures are company-reported."}),
    dict(date="2026-10-28", cat="ai", src="Tom's Hardware",
         url="https://www.tomshardware.com/tech-industry/artificial-intelligence/google-reveals-new-gemini-4-carbon-ai-model-narrowly-beating-claude-opus-5-5-frontier-ai-model-is-also-the-least-likely-to-hallucinate-benchmarks-claim",
         title={"vi": "Google ra mắt Gemini 4 Carbon: đứng đầu Artificial Analysis Intelligence Index V5, nhưng chỉ mở cho nhóm bảo mật trước",
                "en": "Google unveils Gemini 4 Carbon: tops the Artificial Analysis Intelligence Index V5, but access starts with cyber defenders"},
         body={"vi": "Theo Tom's Hardware, Gemini 4 Carbon đạt 59 điểm trên Artificial Analysis Intelligence Index V5, hơn Claude Opus 5.5 một điểm, và đứng nhất ở bốn trong chín hạng mục đánh giá với chi phí mỗi tác vụ thấp hơn các mô hình đứng đầu khác. Google cho phép truy cập trước cho các nhóm phòng thủ an ninh mạng qua chương trình Fairwind; thời điểm mở rộng rãi chưa được công bố. Xếp hạng là của đơn vị đánh giá bên thứ ba nhưng các benchmark khác (SEC-bench Pro, ExploitGym, CWE-bench) do Google báo cáo.",
               "en": "According to Tom's Hardware, Gemini 4 Carbon scores 59 on the Artificial Analysis Intelligence Index V5, one point ahead of Claude Opus 5.5, and ranks first on four of nine evaluations at a lower cost per task than other top models. Google is giving early access to cyber defenders through its Fairwind programme; no date for wider availability has been announced. The ranking comes from a third-party evaluator, while other benchmarks (SEC-bench Pro, ExploitGym, CWE-bench) are Google-reported."}),
    dict(date="2026-10-26", cat="ai", src="LLM Stats",
         url="https://llm-stats.beehiiv.com/p/what-changed-in-ai-last-week-oct-26-nov-1",
         title={"vi": "OpenAI ra mắt GPT-6.1 Terra: giá giảm một nửa so với GPT-6.1 Sol, ngữ cảnh 1,05 triệu token",
                "en": "OpenAI ships GPT-6.1 Terra: half the price of GPT-6.1 Sol, 1.05M-token context"},
         body={"vi": "Theo bản tin LLM Stats, GPT-6.1 Terra là mô hình nhanh cho computer use, thị giác và viết, giá $1 / $5 mỗi triệu token vào / ra (thấp hơn 50% so với GPT-6.1 Sol) và cửa sổ ngữ cảnh 1,05 triệu token. OpenAI cho biết ở mức nỗ lực trung bình nó ngang GPT-6 Astra trên bài đánh giá Agents' Last Exam với giá mỗi token bằng một phần mười. Đây là tuyên bố của OpenAI.",
               "en": "Per the LLM Stats newsletter, GPT-6.1 Terra is a fast model for computer use, vision and writing, priced at $1 / $5 per million input / output tokens (50% below GPT-6.1 Sol) with a 1.05M-token context window. OpenAI says it matches GPT-6 Astra on Agents' Last Exam at medium effort for one-tenth the price per token. That is OpenAI's claim."}),
    dict(date="2026-11-02", cat="mobile", src="Android Central",
         url="https://www.androidcentral.com/phones/xiaomi/xiaomis-going-global-the-18-pro-series-is-preparing-for-a-major-november-launch",
         title={"vi": "Xiaomi xác nhận ra mắt toàn cầu dòng 18 Pro trong tháng 11",
                "en": "Xiaomi confirms global launch of the 18 Pro series in November"},
         body={"vi": "Theo Android Central, Xiaomi xác nhận trên mạng xã hội rằng dòng Xiaomi 18 Pro (ra mắt tại Trung Quốc cuối tháng 9) sẽ có mặt toàn cầu trong tháng 11, nhưng chưa nêu ngày cụ thể. Giá và dung lượng pin bản quốc tế hiện mới chỉ là tin đồn nên chúng tôi không đưa vào đây.",
               "en": "According to Android Central, Xiaomi confirmed on social media that the Xiaomi 18 Pro series (launched in China in late September) will debut globally in November, with no exact date yet. International pricing and battery capacity are still rumours, so they are not included here."}),
]


# ---------------------------------------------------------------------------------------------
# Metadata for article pages: slug, "why it matters" (Shopsmon's own short take, clearly editorial),
# which blog/landing to link, and which affiliate box (see build.py AFF_BOXES) fits the topic.
# ---------------------------------------------------------------------------------------------
META = {
    "https://deepmind.google/blog/agentic-cheminformatics-with-google-antigravity/": dict(
        slug="deepmind-agentic-cheminformatics", aff="agents",
        why={"vi": "Điểm đáng học không nằm ở hoá học mà ở mô hình làm việc: agent nhận một bộ kỹ năng (skills) chuyên ngành, tự chạy phân tích trên dữ liệu thật rồi đề xuất kết quả có thể kiểm chứng. Cùng cấu trúc đó áp dụng được cho nhiều quy trình doanh nghiệp, miễn là có bước con người kiểm tra cuối cùng.",
             "en": "The takeaway is less about chemistry than about the working pattern: an agent receives a domain skill pack, runs analysis on real data and proposes results that can be tested. The same structure fits many business workflows, as long as a human checks the final step."}),
    "https://futurumgroup.com/insights/qualcomm-validates-first-hbc-silicon-with-an-18x-memory-bandwidth-gain-over-lpddr5x/": dict(
        slug="qualcomm-hbc-memory-bandwidth", aff=None,
        why={"vi": "Suy luận LLM thường bị giới hạn bởi băng thông bộ nhớ chứ không phải số phép tính, nên bất kỳ cải tiến băng thông nào cũng đáng theo dõi. Nhưng đây mới là phép đo ở mức thành phần, chưa phải tốc độ sinh token thực tế.",
             "en": "LLM inference is usually bound by memory bandwidth rather than arithmetic, so any bandwidth gain is worth watching. This is still a component-level measurement, not real token-generation speed."}),
    "https://www.nordicsemi.com/Nordic-news/2026/11/Nordic-brings-edge-AI-to-battery-powered-WiFi-devices-20-times-lower-standby-power-with-nRF71-Series": dict(
        slug="nordic-nrf71-edge-ai", aff="iot",
        why={"vi": "Với thiết bị chạy pin, điện năng lúc chờ thường quyết định tuổi thọ sản phẩm. Đưa Wi-Fi, BLE, Thread và một NPU nhỏ lên cùng chip giúp những tác vụ như nhận diện từ khoá hay phát hiện bất thường chạy ngay trên cảm biến, thay vì gửi mọi dữ liệu lên cloud.",
             "en": "For battery-powered devices, standby power often decides product lifetime. Putting Wi-Fi, BLE, Thread and a small NPU on one chip lets jobs like keyword spotting or anomaly detection run on the sensor itself instead of streaming everything to the cloud."}),
    "https://pr.kaist.ac.kr/newsen/html/news/?mng_no=68990&mode=V": dict(
        slug="kaist-cluster-llm-finetuning", aff=None,
        why={"vi": "Fine-tune bớt dữ liệu lặp là cách rẻ nhất để giảm chi phí GPU. Nếu kết quả tái lập được trên mô hình và dữ liệu của bạn, đây là hướng tối ưu thực dụng cho các dự án chatbot chuyên ngành.",
             "en": "Training on less repetitive data is the cheapest way to cut GPU cost. If the result reproduces on your own model and data, it is a practical optimisation for domain-specific chatbot projects."}),
    "https://www.ucl.ac.uk/mathematical-physical-sciences/high-energy-physics/reconstruct-everything-ucls-pioneering-ai-model-could-redefine-particle-physics-reconstruction": dict(
        slug="ucl-rem-particle-reconstruction", aff=None,
        why={"vi": "Tái tạo từ phép đo thô là bài toán chung của vật lý hạt, thị giác máy và tái tạo 3D: thay chuỗi thuật toán chuyên biệt bằng một mô hình học thống nhất. Lưu ý kết quả hiện chỉ trên dữ liệu mô phỏng.",
             "en": "Reconstructing structure from raw measurements is a shared problem across particle physics, computer vision and 3D reconstruction: replace a chain of specialised algorithms with one learned model. Note the results are on simulated data only."}),
    "https://www.zyphra.com/our-work/zyphra-hierarchical-attention": dict(
        slug="zyphra-hierarchical-attention", aff=None,
        why={"vi": "Chi phí attention bậc hai là rào cản lớn của ngữ cảnh dài. Các phương pháp thưa phân cấp như thế này nhắm tới việc giữ chất lượng mà giảm mạnh KV cache cần đọc khi giải mã &mdash; yếu tố quyết định chi phí phục vụ.",
             "en": "Quadratic attention cost is the main barrier to long context. Hierarchical sparse methods like this aim to keep quality while sharply reducing the KV cache read during decoding &mdash; the factor that drives serving cost."}),
    "https://www.mediatek.com/press-room": dict(
        slug="mediatek-ericsson-pre6g", aff=None,
        why={"vi": "Pre-6G cho thấy hướng đi của mạng di động, nhưng với người dùng và nhà phát triển ứng dụng, tác động thực tế còn cách vài năm. Đáng theo dõi hơn là độ trễ và độ ổn định chứ không chỉ tốc độ đỉnh.",
             "en": "Pre-6G shows where mobile networks are heading, but for users and app developers the real impact is still years away. Latency and stability matter more than peak speed."}),
    "https://www.androidauthority.com/motorola-signature-display-camera-specs-revealed-3730578/": dict(
        slug="motorola-signature-27", aff=None,
        why={"vi": "Thông số công bố (độ sáng, zoom) chỉ là điểm xuất phát; trải nghiệm thực tế phải chờ đánh giá độc lập sau khi máy ra mắt ngày 5/11.",
             "en": "Announced specs (brightness, zoom) are only a starting point; real-world performance has to wait for independent reviews after the Nov 5 launch."}),
    "https://badinfluence.news/weekly": dict(
        slug="mistral-large-4-open-weights", aff="agents",
        why={"vi": "Mô hình mã nguồn mở cỡ lớn kèm hỗ trợ vLLM ngay ngày đầu giúp tự triển khai (self-host) trở thành lựa chọn thực tế cho doanh nghiệp có yêu cầu riêng về dữ liệu. Cần tự đo trên tác vụ của mình thay vì tin hoàn toàn vào benchmark của hãng.",
             "en": "A large open-weights model with day-0 vLLM support makes self-hosting a realistic option for companies with data-residency needs. Measure it on your own tasks rather than trusting vendor benchmarks alone."}),
    "https://www.tomshardware.com/tech-industry/artificial-intelligence/google-reveals-new-gemini-4-carbon-ai-model-narrowly-beating-claude-opus-5-5-frontier-ai-model-is-also-the-least-likely-to-hallucinate-benchmarks-claim": dict(
        slug="gemini-4-carbon", aff=None,
        why={"vi": "Chênh lệch một điểm trên một chỉ số tổng hợp chưa nói lên nhiều. Khi chọn mô hình cho sản phẩm, hãy so sánh theo chi phí mỗi tác vụ và độ chính xác trên đúng dữ liệu của bạn.",
             "en": "A one-point gap on an aggregate index says little. When choosing a model for a product, compare cost per task and accuracy on your own data."}),
    "https://llm-stats.beehiiv.com/p/what-changed-in-ai-last-week-oct-26-nov-1": dict(
        slug="gpt-6-1-terra", aff="agents",
        why={"vi": "Giá mỗi token giảm một nửa và ngữ cảnh hơn một triệu token làm thay đổi bài toán chi phí cho chatbot và agent tra cứu tài liệu dài. Vẫn nên kiểm tra tỉ lệ ảo giác trên dữ liệu thật trước khi chuyển đổi.",
             "en": "Half the per-token price plus a context window beyond a million tokens changes the cost equation for chatbots and long-document agents. Still, test the hallucination rate on real data before switching."}),
    "https://www.androidcentral.com/phones/xiaomi/xiaomis-going-global-the-18-pro-series-is-preparing-for-a-major-november-launch": dict(
        slug="xiaomi-18-pro-global", aff=None,
        why={"vi": "Mới có xác nhận về thời điểm (tháng 11); giá và thông số bản quốc tế chưa chính thức nên chưa có gì để kết luận.",
             "en": "Only the timing (November) is confirmed; international pricing and specs are unofficial, so there is nothing to conclude yet."}),
    "https://iot-now.com/2026/11/03/159158-ceva-mobilint-physical-ai-regulus-edge-ai-soc/": dict(
        slug="ceva-mobilint-regulus", aff="iot",
        why={"vi": "10 TOPS dưới 3 W đặt AI thị giác vào tầm của camera thông minh, drone và robot nhỏ. Với dự án AIoT, câu hỏi thực tế là mô hình của bạn có được toolchain của chip hỗ trợ hay không &mdash; ở đây PyTorch/ONNX là điểm cộng.",
             "en": "10 TOPS under 3 W puts vision AI within reach of smart cameras, drones and small robots. For an AIoT project the practical question is whether the chip's toolchain supports your model &mdash; PyTorch/ONNX support is a plus here."}),
    "https://www.newelectronics.co.uk/content/news/brainchip-introduces-akd1500-raspberry-pi-5-development-kit-for-edge-ai-applications": dict(
        slug="brainchip-akd1500-raspberry-pi-5", aff="iot",
        why={"vi": "Bộ kit gắn trên Raspberry Pi giúp thử ý tưởng AI công suất thấp nhanh và rẻ. Nên đo điện năng thực tế trên bài toán của bạn, vì mức tiết kiệm phụ thuộc mạnh vào việc dữ liệu có đủ thưa theo sự kiện hay không.",
             "en": "A kit built on a Raspberry Pi makes it quick and cheap to try low-power AI ideas. Measure real power on your own problem, since savings depend heavily on how sparse your data is in events."}),
    "https://www.matteralpha.com/industry-news/home-assistant-s-matter-server-adds-matter-1-6-1-camera-talkback-ikea-aqara-fp400-support": dict(
        slug="matter-1-6-1-home-assistant", aff="iot",
        why={"vi": "Chuẩn chung như Matter giảm công sức tích hợp cho nhà phát triển IoT, nhưng chuỗi từ đặc tả đến nút bấm trên Home Assistant còn nhiều bước (matter.js, Matter Server, tích hợp, thiết bị). Hãy kiểm tra thiết bị của bạn hỗ trợ phiên bản nào.",
             "en": "A shared standard like Matter reduces integration effort for IoT developers, but there are many steps between the spec and a button in Home Assistant (matter.js, Matter Server, integration, device). Check which version your devices support."}),
    "https://arxiv.org/abs/2611.02332": dict(
        slug="leanguard-verified-agent-guardrails", aff="agents",
        why={"vi": "Khi agent được phép gọi công cụ có tác dụng thật (gửi mail, chuyển tiền, sửa dữ liệu), chính sách cứng kiểm tra trước khi thực thi là lớp bảo vệ cần thiết ngoài prompt. Đây là hướng thiết kế mà chúng tôi cũng áp dụng cho các agent theo yêu cầu: tách &ldquo;đề xuất hành động&rdquo; khỏi &ldquo;được phép thực thi&rdquo;.",
             "en": "When an agent may call tools with real effects (send email, move money, edit data), a hard policy check before execution is a necessary layer beyond prompting. It is also a design we apply to custom agents: separate &ldquo;proposing an action&rdquo; from &ldquo;being allowed to execute it&rdquo;."}),
    "https://arxiv.org/abs/2611.03618": dict(
        slug="strategist-evolving-inference-strategies", aff="agents",
        why={"vi": "Ý tưởng cốt lõi &mdash; tách mô hình khỏi chiến lược suy luận và coi chiến lược là mã có thể tái sử dụng &mdash; khớp với thực tế xây agent: phần lớn chất lượng và chi phí nằm ở vòng điều phối chứ không chỉ ở mô hình.",
             "en": "The core idea &mdash; separating the model from the inference strategy and treating the strategy as reusable code &mdash; matches how agents are built in practice: much of the quality and cost sits in the orchestration loop, not just the model."}),
}
for _n in NEWS:
    _m = META[_n["url"]]
    _n["slug"] = _m["slug"]
    _n["why"] = _m["why"]
    _n["aff"] = _m["aff"]
assert len({n["slug"] for n in NEWS}) == len(NEWS)